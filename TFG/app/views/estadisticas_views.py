from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from app.models import User, Partido, Equipo, Cancha 
from django.db.models import Count, F, Q

class EstadisticasView(LoginRequiredMixin, TemplateView):
    template_name = 'estadisticas/estadisticas_generales.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Estadísticas de la Comunidad"

        # --- 1. Jugadores con más elo ---
        context['top_elo_jugadores'] = User.objects.filter(
            is_active=True
        ).order_by('-calificacion')[:10]

        # --- 2. Jugadores mas partidos jugados ---
        # partidos_jugados' del modelo User.
        context['top_jugadores_activos'] = User.objects.filter(
            is_active=True,
            partidos_jugados__gt=0
        ).order_by('-partidos_jugados', '-calificacion')[:10]

        # --- 3. Equipos PERMANENTES con más Victorias ---
        context['top_equipos_activos'] = Equipo.objects.filter(
            tipo_equipo='PERMANENTE', 
            activo=True,
            partidos_jugados_permanente__gt=0
        ).order_by('-victorias_permanente', '-partidos_jugados_permanente')[:10]

        # --- 4. Canchas con más partidos jugados ---
        context['top_canchas_populares'] = Cancha.objects.filter(
            disponible=True
        ).annotate(
            num_partidos_cancha=Count(
                'get_cancha_partido',
                filter=Q(get_cancha_partido__estado='FINALIZADO')
            )
        ).filter(num_partidos_cancha__gt=0).order_by('-num_partidos_cancha')[:10]
            
        return context