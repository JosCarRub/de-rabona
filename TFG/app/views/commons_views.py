from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from app.models import Partido, User
from django.db.models import Q

# LANDING
class Landing(TemplateView):
    template_name = 'global/landing_page.html'


#HOME
class Home(LoginRequiredMixin, TemplateView):
    template_name = 'global/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_actual = self.request.user
        ahora = timezone.now()

        context['titulo_pagina'] = f"Bienvenido, {usuario_actual.nombre}"

        proximos_partidos_query = Partido.objects.filter(
            Q(jugadores=usuario_actual) | Q(creador=usuario_actual),
            estado__in=['PROGRAMADO', 'EN_CURSO'],
            fecha__gte=ahora
        ).distinct().select_related('cancha').order_by('fecha')[:3] 

        proximos_partidos_info = []
        for partido in proximos_partidos_query:
            proximos_partidos_info.append({
                'partido': partido,
                'es_creador': (partido.creador == usuario_actual),
                'plazas_disponibles': partido.max_jugadores - partido.jugadores.count(),
                'inscripcion_esta_abierta': partido.inscripcion_abierta
            })
        context['proximos_partidos_dashboard'] = proximos_partidos_info
        
        # 3. Actividad Reciente
        ultimo_partido_jugado = Partido.objects.filter(
        Q(jugadores=usuario_actual) | Q(creador=usuario_actual),
        estado='FINALIZADO'
        ).distinct().order_by('-fecha').first()
        context['ultimo_partido_jugado'] = ultimo_partido_jugado



        return context
    
class InfoEstadoEquipoView(TemplateView):
    """
    Vista para mostrar la página informativa sobre el estado "activo/inactivo" de los equipos.
    """
    template_name = 'global/info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Política de Estado de Equipos"
        context['email_contacto'] = "derabona@admin.com"
        return context
    
class DashboardAdmin(TemplateView):
    template_name = 'secret/dashboard.html'

class DashboardAdminVoice(TemplateView):
    template_name = 'secret/dashboard_voice.html'

