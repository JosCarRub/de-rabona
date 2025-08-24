from django.views.generic import CreateView,UpdateView, ListView, DetailView, View, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, LoginRequiredMixin, UserPassesTestMixin

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from app.forms.equipo_forms import EquipoCreateForm, EquipoUpdateForm, InvitarMiembroForm
from app.models.equipo import Equipo
from app.models.invitacion import InvitacionEquipo
from app.models.user import User
from django.views.generic.edit import FormMixin 

class CrearEquipoPermanenteView(LoginRequiredMixin, CreateView):
    model = Equipo
    form_class = EquipoCreateForm
    template_name = 'equipos/crear_equipo_permanente.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # Pasar usuario al form para filtrar miembros_iniciales
        return kwargs

    def form_valid(self, form):
        # crea la instancia del equipo en memoria, pero NO en bbdd aún
        self.object = form.save(commit=False)
        
        self.object.capitan = self.request.user
        self.object.tipo_equipo = 'PERMANENTE'
        self.object.activo = True 

        # guarda el objeto Equipo principal en la base de datos.

        self.object.save()

        # guardar las relaciones ManyToMany 

        form.save_m2m()

        self.object.jugadores.add(self.request.user)
        
        messages.success(self.request, f"¡Equipo '{self.object.nombre_equipo}' creado con éxito!")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('detalle_equipo', kwargs={'pk': self.object.id_equipo})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Crear Nuevo Equipo Permanente"
        return context

class MisEquiposListView(LoginRequiredMixin, ListView):
    model = Equipo
    template_name = 'equipos/mis_equipos_lista.html'
    context_object_name = 'equipos_list'
    paginate_by = 12

    def get_queryset(self):
        usuario = self.request.user
        
        # Si el usuario es un superusuario, TODOS los equipos
        if usuario.is_superuser:
            queryset = Equipo.objects.filter(
                tipo_equipo='PERMANENTE'
            ).distinct().order_by('-fecha_creacion')
        else:
            queryset = Equipo.objects.filter(
                tipo_equipo='PERMANENTE',
                activo=True 
            ).filter(
                Q(capitan=usuario) | Q(jugadores=usuario)
            ).distinct().order_by('-fecha_creacion')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Mis Equipos"
        context['is_admin_view'] = self.request.user.is_superuser

        return context

class DetalleEquipoView(LoginRequiredMixin, DetailView):
    model = Equipo
    template_name = 'equipos/detalle_equipo.html'
    context_object_name = 'equipo'
    pk_url_kwarg = 'pk' # Coincide con <uuid:pk> en tu URL

    def get_queryset(self):
        usuario = self.request.user
        
        base_queryset = super().get_queryset().filter(tipo_equipo='PERMANENTE')

        if not usuario.is_superuser:
            return base_queryset.filter(activo=True)
        
        return base_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipo = self.get_object()
        context['titulo_pagina'] = f"Perfil del Equipo: {equipo.nombre_equipo}"
        context['es_capitan'] = (equipo.capitan == self.request.user)
        context['es_miembro'] = self.request.user in equipo.jugadores.all()

        context['is_admin_view'] = self.request.user.is_superuser
        
        return context

class EditarEquipoPermanenteView(LoginRequiredMixin, UpdateView):
    model = Equipo
    form_class = EquipoUpdateForm  
    template_name = 'equipos/editar_equipo_permanente.html'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return super().get_queryset().filter(
            capitan=self.request.user, 
            tipo_equipo='PERMANENTE', 
            activo=True
        )
    

    def form_valid(self, form):
        messages.success(self.request, f"La información del equipo '{form.instance.nombre_equipo}' ha sido actualizada con éxito.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('detalle_equipo', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Editar: {self.object.nombre_equipo}"
        context['equipo'] = self.object
        return context
    
class AbandonarEquipoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        equipo = get_object_or_404(Equipo, pk=kwargs['pk'])
        usuario = request.user

        # es miembro del equipo?
        if not equipo.jugadores.filter(pk=usuario.pk).exists():
            messages.error(request, "No eres miembro de este equipo.")
            return redirect('detalle_equipo', pk=equipo.pk)

        # es capitán?
        if equipo.capitan == usuario:
            messages.error(request, "El capitán no puede abandonar el equipo. Debes eliminar el equipo o transferir la capitanía.")
            return redirect('detalle_equipo', pk=equipo.pk)

        # Eliminar al jugador del equipo
        equipo.jugadores.remove(usuario)
        
        messages.success(request, f"Has abandonado el equipo '{equipo.nombre_equipo}'.")
        return redirect('lista_mis_equipos')
    
class EliminarEquipoView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Equipo
    template_name = 'equipos/equipo_confirm_delete.html' 
    success_url = reverse_lazy('lista_mis_equipos') 
    context_object_name = 'equipo'

    def test_func(self):
        """Solo el capitán puede eliminar el equipo."""
        equipo = self.get_object()
        return equipo.capitan == self.request.user

    def form_valid(self, form):
        messages.success(self.request, f"El equipo '{self.object.nombre_equipo}' ha sido eliminado permanentemente.")
        return super().form_valid(form)

##---------------------------INVITACION------------------------------------------------------

class GestionarMiembrosView(LoginRequiredMixin, UserPassesTestMixin, FormMixin, DetailView):
    model = Equipo
    template_name = 'equipos/gestionar_miembros.html'
    context_object_name = 'equipo'
    pk_url_kwarg = 'pk'
    form_class = InvitarMiembroForm

    def test_func(self):
        """Asegura que solo el capitán pueda acceder."""
        equipo = self.get_object()
        return equipo.capitan == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipo = self.get_object()
        context['titulo_pagina'] = f"Gestionar: {equipo.nombre_equipo}"
        context['miembros'] = equipo.jugadores.all().order_by('nombre')
        context['invitaciones_pendientes'] = equipo.invitaciones.filter(estado='PENDIENTE')
        # El formulario se añade automáticamente por FormMixin
        return context

    def get_form_kwargs(self):
        """Pasa el equipo y el usuario actual al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['equipo'] = self.get_object()
        kwargs['invitador'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        """Maneja las acciones POST (invitar o eliminar)."""
        self.object = self.get_object() # Necesario para FormMixin

        # --- Lógica para ELIMINAR un miembro ---
        if 'eliminar_miembro' in request.POST:
            miembro_id = request.POST.get('miembro_id')
            try:
                miembro_a_eliminar = self.object.jugadores.get(pk=miembro_id)
                if miembro_a_eliminar == self.object.capitan:
                    messages.error(request, "No puedes eliminar al capitán del equipo.")
                else:
                    self.object.jugadores.remove(miembro_a_eliminar)
                    messages.warning(request, f"{miembro_a_eliminar.nombre} ha sido eliminado del equipo.")
            except User.DoesNotExist:
                messages.error(request, "El miembro que intentas eliminar no existe.")
            return redirect('gestionar_miembros', pk=self.object.pk)

        # --- Lógica para INVITAR un miembro ---
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """Se ejecuta si el formulario de invitación es válido."""
        usuario_a_invitar = form.cleaned_data.get('email')
        
        InvitacionEquipo.objects.create(
            equipo=self.get_object(),
            invitado_por=self.request.user,
            invitado=usuario_a_invitar
        )
        
        messages.success(self.request, f"¡Invitación enviada a {usuario_a_invitar.nombre}!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirige a la misma página después de una acción exitosa."""
        return reverse('gestionar_miembros', kwargs={'pk': self.object.pk})
    
class ToggleActivoEquipoView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        equipo = get_object_or_404(Equipo, pk=kwargs['pk'])

        equipo.activo = not equipo.activo
        equipo.save(update_fields=['activo'])

        estado_str = "activado" if equipo.activo else "desactivado"
        messages.success(request, f"El equipo '{equipo.nombre_equipo}' ha sido {estado_str}.")
        
        return redirect('lista_mis_equipos')
