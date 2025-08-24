from django.contrib import messages
from django.urls import reverse_lazy
from app.forms.canchas_forms import CanchasForm
from app.models.cancha import Cancha
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone as now_timezone


from app.models.partido import Partido

#CANCHAS



class CanchasView(LoginRequiredMixin, ListView):
    model = Cancha
    template_name = 'canchas/canchas_lista.html' 
    context_object_name = 'canchas_list'
    paginate_by = 9 

    def get_queryset(self):
        
        return Cancha.objects.filter(disponible=True).order_by('nombre_cancha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Descubre Nuestras Canchas"
        return context
    
class RegistrarCanchaView(LoginRequiredMixin, CreateView):
    model = Cancha
    form_class = CanchasForm
    template_name = 'canchas/registro_canchas.html' 
    success_url = reverse_lazy('canchas_lista') 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Registrar Nueva Cancha"
        return context

    def form_valid(self, form):
        
        cancha = form.save()
        messages.success(self.request, f"¡Cancha '{cancha.nombre_cancha}' registrada con éxito!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Hubo errores al registrar la cancha. Por favor, revisa el formulario.")
        return super().form_invalid(form)

class DetalleCanchaView(LoginRequiredMixin, DetailView):
    model = Cancha
    template_name = 'canchas/detalle_cancha.html' 
    context_object_name = 'cancha'
    pk_url_kwarg = 'pk_cancha' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cancha = self.get_object()
        context['titulo_pagina'] = f"Detalles de la Cancha: {cancha.nombre_cancha}"
        
        # Próximos partidos en esta cancha
        context['proximos_partidos'] = Partido.objects.filter(
            cancha=cancha,
            fecha__gte=now_timezone.now(), 
            estado='PROGRAMADO'
        ).order_by('fecha')[:10] 

        
        return context