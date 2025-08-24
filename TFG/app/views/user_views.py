from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView,CreateView,UpdateView, View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout


from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.db import transaction

from app.forms.user_forms import UserRegisterForm, UserUpdateProfilelForm
from app.models.equipo import Equipo
from app.models.invitacion import InvitacionEquipo
from app.models.user import User



#REGISTRO
class UserRegister(CreateView):
    form_class = UserRegisterForm
    template_name = 'auth/registration.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        
        return super().form_valid(form)
    
    


#PERFIL
class Perfil(LoginRequiredMixin, TemplateView):
    model = User
    template_name = 'perfil/perfil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Determinar rango actual basado en ELO
        current_rank = self.get_rank_name(user.calificacion)
        
        # Calcular estadísticas adicionales
        total_partidos = user.partidos_jugados or 0
        win_rate = 0
        if total_partidos > 0:
            win_rate = round((user.victorias / total_partidos) * 100, 1)
        
        context.update({
            'current_rank': current_rank,
            'win_rate': win_rate,
            'rank_info': self.get_rank_info(user.calificacion),
        })
        
        return context
    
    def get_rank_name(self, elo):
        """Determina el nombre del rango basado en el ELO"""
        if elo >= 2000:
            return "Leyenda"
        elif elo >= 1800:
            return "Diamante"
        elif elo >= 1600:
            return "Platino"
        elif elo >= 1400:
            return "Oro"
        elif elo >= 1200:
            return "Plata"
        else:
            return "Bronce"
    
    def get_rank_info(self, elo):
        """Obtiene información detallada del rango actual"""
        ranks = [
            {'name': 'Bronce', 'min_elo': 0, 'max_elo': 1199, 'color': '#cd7f32', 'icon': '🛡️'},
            {'name': 'Plata', 'min_elo': 1200, 'max_elo': 1399, 'color': '#c0c0c0', 'icon': '⚔️'},
            {'name': 'Oro', 'min_elo': 1400, 'max_elo': 1599, 'color': '#ffd700', 'icon': '🏆'},
            {'name': 'Platino', 'min_elo': 1600, 'max_elo': 1799, 'color': '#e5e4e2', 'icon': '👑'},
            {'name': 'Diamante', 'min_elo': 1800, 'max_elo': 1999, 'color': '#b9f2ff', 'icon': '💎'},
            {'name': 'Leyenda', 'min_elo': 2000, 'max_elo': 9999, 'color': '#ff6b35', 'icon': '⭐'},
        ]
        
        current_rank = None
        next_rank = None
        
        for i, rank in enumerate(ranks):
            if rank['min_elo'] <= elo <= rank['max_elo']:
                current_rank = rank
                if i < len(ranks) - 1:
                    next_rank = ranks[i + 1]
                break
        
        if current_rank is None:
            current_rank = ranks[0]  # Por defecto Bronce
        
        # Calcular progreso hacia el siguiente rango
        progress = 0
        elo_needed = 0
        if next_rank:
            range_size = next_rank['min_elo'] - current_rank['min_elo']
            current_progress = elo - current_rank['min_elo']
            progress = (current_progress / range_size) * 100 if range_size > 0 else 0
            elo_needed = next_rank['min_elo'] - elo
        
        return {
            'current': current_rank,
            'next': next_rank,
            'progress': max(0, min(100, progress)),
            'elo_needed': max(0, elo_needed),
        }

class UserUpdateProfile(LoginRequiredMixin, UpdateView):

    model = User
    form_class = UserUpdateProfilelForm
    template_name = 'perfil/update_profile.html'
    success_url = reverse_lazy('perfil')

    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):

        messages.success(self.request, '¡Tu perfil ha sido actualizado con éxito!')

        return super().form_valid(form)
    
    def form_invalid(self, form):

        messages.error(self.request, 'No ha sido posible actuliazar tu perfil, revisa los campos que has querido actulizar por que debe haber un error.')

        return super().form_invalid(form)


class MisInvitacionesView(LoginRequiredMixin, ListView):
    model = InvitacionEquipo
    template_name = 'global/mis_invitaciones.html'
    context_object_name = 'invitaciones'

    def get_queryset(self):
        """Muestra solo las invitaciones pendientes para el usuario logueado."""
        return InvitacionEquipo.objects.filter(
            invitado=self.request.user, 
            estado='PENDIENTE'
        ).select_related('equipo', 'invitado_por')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Mis Invitaciones a Equipos"
        return context

class ResponderInvitacionView(LoginRequiredMixin, View):
    
    def post(self, request, *args, **kwargs):
        """
        Maneja la acción de aceptar o rechazar una invitación a través de POST.
        """
        # Obtenemos la invitación
        invitacion = get_object_or_404(
            InvitacionEquipo, 
            pk=kwargs['pk'], 
            invitado=request.user, 
            estado='PENDIENTE'
        )
        
        
        accion = kwargs.get('accion')

        if accion == 'aceptar':
            # Lógica para aceptar la invitación
            invitacion.equipo.jugadores.add(request.user)
            invitacion.estado = 'ACEPTADA'
            messages.success(request, f"¡Te has unido al equipo '{invitacion.equipo.nombre_equipo}'!")
        
        elif accion == 'rechazar':
            # Lógica para rechazar la invitación
            invitacion.estado = 'RECHAZADA'
            messages.info(request, f"Has rechazado la invitación para unirte a '{invitacion.equipo.nombre_equipo}'.")
        
        else:
            # Si la acción no es válida, mostramos un error.
            messages.error(request, "Acción no válida.")
            return redirect('mis_invitaciones')

        invitacion.fecha_respuesta = timezone.now()
        invitacion.save()
        
        return redirect('mis_invitaciones')

    def get(self, request, *args, **kwargs):
        
        messages.warning(request, "Para responder a una invitación, por favor usa los botones correspondientes.")
        return redirect('mis_invitaciones')

class EliminarCuentaView(LoginRequiredMixin, TemplateView):
    template_name = 'perfil/eliminar_cuenta.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Confirmar Eliminación de Cuenta"
        
        context['equipos_capitaneados'] = Equipo.objects.filter(capitan=self.request.user, tipo_equipo='PERMANENTE')
        return context

    @transaction.atomic 
    def post(self, request, *args, **kwargs):
        usuario_a_eliminar = request.user

        # 1. Gestionar los equipos de los que es capitán
        equipos_capitaneados = Equipo.objects.filter(capitan=usuario_a_eliminar, tipo_equipo='PERMANENTE')

        for equipo in equipos_capitaneados:
            # Obtenemos los otros miembros del equipo, excluyendo al capitán
            otros_miembros = equipo.jugadores.exclude(pk=usuario_a_eliminar.pk).order_by('date_joined')

            if otros_miembros.exists():
                # CASO A: Hay más miembros. Promocionamos al primero de la lista.
                nuevo_capitan = otros_miembros.first()
                equipo.capitan = nuevo_capitan
                equipo.save()
                
            
            else:
                # CASO B: No hay más miembros. El equipo se elimina.
                nombre_equipo_eliminado = equipo.nombre_equipo
                equipo.delete()
                print(f"INFO: El equipo '{nombre_equipo_eliminado}' ha sido eliminado porque no tenía más miembros.")

        # 2. Proceder con la eliminación del usuario
        try:
            # Cerramos la sesión del usuario
            logout(request)
            
            # Eliminamos el objeto de usuario
            usuario_a_eliminar.delete()
            
            
            return redirect('login') 

        except Exception as e:
            
            messages.error(request, f"Ocurrió un error inesperado al intentar eliminar tu cuenta: {e}")
            return redirect('perfil')
    
