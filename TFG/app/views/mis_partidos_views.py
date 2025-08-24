from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from app.models.partido import Partido
from django.utils import timezone as django_timezone
from django.db.models import Q 


class MisPartidosView(LoginRequiredMixin, ListView):
    model = Partido
    template_name = 'partidos/mis_partidos.html'
    context_object_name = 'partidos_list'
    paginate_by = 10 

    def get_queryset(self):
        return Partido.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_actual = self.request.user
        ahora = django_timezone.now()

     
        partidos_del_usuario = Partido.objects.filter(
            Q(jugadores=usuario_actual) | Q(creador=usuario_actual)
        ).distinct().select_related(
            'cancha', 'creador', 'equipo_local', 'equipo_visitante', 'get_partido_resultado'
        ).prefetch_related('jugadores').order_by('fecha')

        context['proximos_partidos'] = partidos_del_usuario.filter(
            Q(estado='PROGRAMADO') | Q(estado='EN_CURSO'),
            fecha__gte=ahora
        ).order_by('fecha')

        context['partidos_jugados'] = partidos_del_usuario.filter(
            Q(estado='FINALIZADO') | Q(fecha__lt=ahora, estado__in=['PROGRAMADO', 'EN_CURSO', 'CANCELADO'])
        ).order_by('-fecha')
        
        proximos_info = []
        for partido in context['proximos_partidos']:
            proximos_info.append({
                'partido': partido,
                'es_creador': (partido.creador == usuario_actual),
                'plazas_disponibles': partido.max_jugadores - partido.jugadores.count(),
                'inscripcion_esta_abierta': partido.inscripcion_abierta
            })
        context['proximos_partidos_info'] = proximos_info

        historial_info = []
        for partido in context['partidos_jugados']:
            resultado_str = "No finalizado"
            if partido.estado == 'FINALIZADO':
                
                if hasattr(partido, 'get_partido_resultado') and partido.get_partido_resultado:
                    resultado = partido.get_partido_resultado
                    resultado_str = f"{resultado.goles_local} : {resultado.goles_visitante}"
                else:
                    resultado_str = "Resultado no registrado"

            historial_info.append({
                'partido': partido,
                'es_creador': (partido.creador == usuario_actual),
                'resultado_str': resultado_str
            })
        context['partidos_jugados_info'] = historial_info

        context['titulo_pagina'] = "Mis Partidos"
        return context