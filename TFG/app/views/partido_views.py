from datetime import timedelta
import uuid
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView,CreateView,UpdateView, ListView, DetailView, View, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Case, When, BooleanField
from django.db.models import F as FunctionF
from django.db.models import Q as FunctionQ
from django.shortcuts import get_object_or_404, redirect
from datetime import timezone as django_timezone
from django.utils import timezone as now_timezone
from django.contrib.auth import get_user_model
from app.forms.equipo_forms import AsignarEquiposForm
from app.models.equipo import Equipo
from app.models.inscripcion import Inscripcion
from app.models.user import User
from app.forms.partido_forms import PartidoForm, ResultadoPartidoForm
from app.models.partido import Partido
from django.db.models import ExpressionWrapper, DateTimeField
from django.core.exceptions import ValidationError
from django.db import transaction






#PARTIDOS
'''
CrearPartidos

BuscarPartidos

DetallePartidoView

InscribirsePartido

RegistrarResultadoPartidoView
'''



User = get_user_model() 

class CrearPartidos(LoginRequiredMixin, CreateView):
    model = Partido
    form_class = PartidoForm
    template_name = 'partidos/crear_partidos.html'
    
    def get_form_kwargs(self):
        """Pasa el usuario actual al formulario para filtrar sus equipos."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        Procesa el formulario válido, distinguiendo la lógica para
        Partidos Abiertos y Retos de Equipo.
        """
        form.instance.creador = self.request.user
        form.instance.fecha = form.cleaned_data['fecha']
        
        equipo_local_seleccionado = form.cleaned_data.get('equipo_local')

        if equipo_local_seleccionado:
            form.instance.equipo_local = equipo_local_seleccionado
            
            
            tipo_partido_map = {'SALA': 10, 'F7': 14, 'F11': 22}
            form.instance.max_jugadores = tipo_partido_map.get(form.cleaned_data.get('tipo'), 2)
            
            form.instance.tipo_partido = 'CLUB_VS_CLUB'
        else:
            form.instance.max_jugadores = form.cleaned_data.get('max_jugadores')
            form.instance.tipo_partido = 'ABIERTO'

        response = super().form_valid(form)
        
        if self.object:
            if equipo_local_seleccionado:
                self.object.jugadores.set(equipo_local_seleccionado.jugadores.all())
            else:
                self.object.jugadores.add(self.request.user)
        
        messages.success(self.request, "¡Partido creado con éxito!")
        return response

    def get_success_url(self):
        """Redirige al detalle del partido recién creado."""
        return reverse_lazy('detalle_partido', kwargs={'pk': self.object.id_partido})

    def get_context_data(self, **kwargs):
        """Añade el título de la página al contexto."""
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Crear Nuevo Partido"
        return context

    

class BuscarPartidos(LoginRequiredMixin, ListView):
    model = Partido
    template_name = 'partidos/buscar_partidos.html'
    context_object_name = 'partidos_info_list'
    paginate_by = 9

    def get_queryset(self):
        ahora = now_timezone.now()
        tipo_filtro = self.request.GET.get('tipo', None)

        queryset = Partido.objects.filter(
            estado='PROGRAMADO'
        ).annotate(
            limite_inscripcion_calculada=Case(
                When(fecha_limite_inscripcion__isnull=False, then=FunctionF('fecha_limite_inscripcion')),
                default=ExpressionWrapper(FunctionF('fecha') - timedelta(hours=1), output_field=DateTimeField())
            )
        ).filter(
            limite_inscripcion_calculada__gt=ahora
        )

        if tipo_filtro == 'abierto':
            queryset = queryset.filter(FunctionQ(equipo_local__isnull=True) | ~FunctionQ(equipo_local__tipo_equipo='PERMANENTE'))
        elif tipo_filtro == 'reto':
            queryset = queryset.filter(equipo_local__isnull=False, equipo_local__tipo_equipo='PERMANENTE')
        
        queryset = queryset.annotate(num_jugadores_inscritos=Count('jugadores'))
        
        return queryset.order_by('fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context['titulo_pagina'] = "Encuentra Partidos"
        
        partidos_procesados = []
        usuario_actual_id = self.request.user.id

        
        partidos_inscritos_ids = set(
            self.request.user.get_jugadores_partido.values_list('id_partido', flat=True)
        )

        for partido in context['partidos_info_list']:
           
            
            plazas_disponibles = partido.max_jugadores - partido.num_jugadores_inscritos
            
            # La inscripción está abierta si hay plazas
            inscripcion_esta_abierta = plazas_disponibles > 0

            partidos_procesados.append({
                'partido': partido,
                'es_creador': (partido.creador_id == usuario_actual_id),
                'esta_inscrito': partido.id_partido in partidos_inscritos_ids,
                'inscripcion_esta_abierta': inscripcion_esta_abierta,
                'plazas_disponibles': plazas_disponibles,
            })
            
        context['partidos_info_list'] = partidos_procesados
        context['tipo_filtro'] = self.request.GET.get('tipo', 'todos')
        return context


class DetallePartidoView(LoginRequiredMixin, DetailView):
    model = Partido
    template_name = 'partidos/detalle_partido.html'
    context_object_name = 'partido'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        partido = self.get_object()
        usuario_actual = self.request.user

        context['titulo_pagina'] = f"Detalles: {partido.cancha.nombre_cancha} - {partido.fecha.strftime('%d/%m %H:%M')}"
        context['es_creador'] = (partido.creador == usuario_actual)
        
        context['esta_inscrito'] = partido.jugadores.filter(id=usuario_actual.id).exists()
        context['inscripcion_esta_abierta'] = partido.inscripcion_abierta
        context['plazas_disponibles'] = partido.max_jugadores - partido.jugadores.count()
        
        jugadores_inscritos_list = partido.jugadores.all().order_by('nombre')
        context['jugadores_inscritos_list'] = jugadores_inscritos_list

        if partido.es_reto_de_equipo:
            context['solicitudes_de_equipos'] = Inscripcion.objects.filter(
                partido=partido, tipo='EQUIPO_PARTIDO', estado='PENDIENTE'
            ).select_related('equipo')
            context['equipos_capitaneados'] = Equipo.objects.filter(
                capitan=usuario_actual,
                tipo_equipo='PERMANENTE',
                activo=True
            ).exclude(id_equipo=partido.equipo_local_id if partido.equipo_local else None)
        else:
            if context['es_creador'] and partido.estado == 'PROGRAMADO':
                context['inscripciones_pendientes'] = Inscripcion.objects.filter(
                    partido=partido, tipo='JUGADOR_PARTIDO', estado='PENDIENTE'
                ).select_related('jugador').order_by('fecha_inscripcion')
        
        return context

    def post(self, request, *args, **kwargs):
        partido = self.get_object()
        usuario_actual = request.user

        if partido.creador != usuario_actual:
            messages.error(request, "No tienes permiso para modificar este partido.")
            return redirect('detalle_partido', pk=partido.pk)

        if partido.estado != 'PROGRAMADO':
            messages.error(request, "Solo se pueden asignar equipos a partidos programados.")
            return redirect('detalle_partido', pk=partido.pk)

        jugadores_local_ids_str = request.POST.get('equipo_local_jugadores', '')
        jugadores_visitante_ids_str = request.POST.get('equipo_visitante_jugadores', '')

        jugadores_local_ids = [int(uid) for uid in jugadores_local_ids_str.split(',') if uid]
        jugadores_visitante_ids = [int(uid) for uid in jugadores_visitante_ids_str.split(',') if uid]

        jugadores_inscritos_ids = set(partido.jugadores.values_list('id', flat=True))
        if not set(jugadores_local_ids).issubset(jugadores_inscritos_ids) or \
           not set(jugadores_visitante_ids).issubset(jugadores_inscritos_ids):
            messages.error(request, "Error: Se intentó asignar un jugador que no está inscrito en el partido.")
            return redirect('detalle_partido', pk=partido.pk)

        with transaction.atomic():
            sufijo_nombre = f"{partido.cancha.nombre_cancha[:10]}_{partido.fecha.strftime('%d%m%y')}"

            equipo_local, _ = Equipo.objects.update_or_create(
                partido_asociado=partido,
                nombre_equipo__startswith='Locales -',
                defaults={
                    'nombre_equipo': f"Locales - {sufijo_nombre}",
                    'capitan': partido.creador,
                    'tipo_equipo': 'PARTIDO'
                }
            )
            equipo_local.jugadores.set(User.objects.filter(id__in=jugadores_local_ids))
            partido.equipo_local = equipo_local

            equipo_visitante, _ = Equipo.objects.update_or_create(
                partido_asociado=partido,
                nombre_equipo__startswith='Visitantes -',
                defaults={
                    'nombre_equipo': f"Visitantes - {sufijo_nombre}",
                    'capitan': partido.creador,
                    'tipo_equipo': 'PARTIDO'
                }
            )
            equipo_visitante.jugadores.set(User.objects.filter(id__in=jugadores_visitante_ids))
            partido.equipo_visitante = equipo_visitante
            
            partido.save()
        
        messages.success(request, "Equipos para el partido asignados correctamente.")
        return redirect('detalle_partido', pk=partido.pk)



    
class InscribirsePartidoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        partido_id = kwargs.get('partido_id')
        partido = get_object_or_404(Partido, id_partido=partido_id, estado='PROGRAMADO')
        usuario = request.user

        inscripcion_existente = Inscripcion.objects.filter(
            jugador=usuario,
            partido=partido,
            tipo='JUGADOR_PARTIDO' 
        ).first()

        if inscripcion_existente:
            if inscripcion_existente.estado == 'ACEPTADA':
                 messages.info(request, "Ya estás inscrito y aceptado en este partido.")
            elif inscripcion_existente.estado == 'PENDIENTE':
                 messages.info(request, "Ya tienes una solicitud de inscripción pendiente para este partido.")
            else: 
                 messages.warning(request, f"Ya existe un registro de tu inscripción con estado '{inscripcion_existente.get_estado_display()}' para este partido.")

            return redirect('detalle_partido', pk=partido.id_partido) 

        if partido.jugadores.count() >= partido.max_jugadores:
            messages.error(request, "Lo sentimos, este partido ya está lleno y no acepta más inscripciones.")
            return redirect('buscar_partidos') 

        try:
            nueva_inscripcion = Inscripcion.objects.create(
                tipo='JUGADOR_PARTIDO',
                jugador=usuario,
                partido=partido,
                estado='PENDIENTE',
            )

            partido.jugadores.add(usuario)

            messages.success(request, f"¡Tu solicitud de inscripción para el partido en {partido.cancha.nombre_cancha} ha sido enviada! Esperando aprobación.")


        except Exception as e:
            
            messages.error(request, f"Ocurrió un error al procesar tu inscripción: {e}")
            
        return redirect('detalle_partido', pk=partido.id_partido) 
    

    
class RegistrarResultadoPartidoView(LoginRequiredMixin, FormView):
    form_class = ResultadoPartidoForm
    template_name = 'partidos/registrar_resultado.html' 

    def dispatch(self, request, *args, **kwargs):
        self.partido = get_object_or_404(Partido, id_partido=kwargs['pk'])
        if self.partido.creador != request.user:
            messages.error(request, "No tienes permiso para registrar el resultado de este partido.")
            return redirect('detalle_partido', pk=self.partido.id_partido)
        if self.partido.estado == 'FINALIZADO':
            messages.info(request, "Este partido ya ha finalizado y tiene un resultado registrado.")
            return redirect('detalle_partido', pk=self.partido.id_partido)
        if self.partido.estado == 'CANCELADO':
            messages.warning(request, "No se puede registrar resultado para un partido cancelado.")
            return redirect('detalle_partido', pk=self.partido.id_partido)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partido'] = self.partido
        context['titulo_pagina'] = f"Registrar Resultado para: Partido en {self.partido.cancha.nombre_cancha}"

        if hasattr(self.partido, 'get_partido_resultado'):
            resultado = self.partido.get_partido_resultado
            context['form'].fields['goles_local'].initial = resultado.goles_local
            context['form'].fields['goles_visitante'].initial = resultado.goles_visitante
        return context

    def form_valid(self, form):
        goles_local = form.cleaned_data['goles_local']
        goles_visitante = form.cleaned_data['goles_visitante']

        try:
            self.partido.registrar_resultado_y_actualizar_stats(goles_local, goles_visitante)
            
            if self.partido.modalidad != 'AMISTOSO' and self.partido.equipo_local and self.partido.equipo_visitante:
                messages.success(self.request, "Resultado registrado y calificaciones ELO actualizadas.")
            elif self.partido.modalidad == 'AMISTOSO':
                messages.success(self.request, "Resultado del partido amistoso registrado (ELO no afectado).")
            else:
                messages.warning(self.request, "Resultado registrado, pero no se pudieron actualizar las calificaciones ELO (faltan equipos o es amistoso).")
        
        except ValidationError as e:
            messages.error(self.request, e.message)
        
        return redirect('detalle_partido', pk=self.partido.id_partido)

    def get_success_url(self):
        return reverse_lazy('detalle_partido', kwargs={'pk': self.partido.id_partido})

##------------------------------------------------- INSCRIPCIONES -------------------------------------------------


class AceptarInscripcionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs): 
        partido_id = kwargs.get('pk') 
        inscripcion_id = kwargs.get('inscripcion_id')

        partido = get_object_or_404(Partido, id_partido=partido_id)
        usuario_actual = request.user

        # ver si el usuario actual es el creador del partido
        if partido.creador != usuario_actual:
            messages.error(request, "No tienes permiso para aceptar inscripciones en este partido.")
            return redirect('detalle_partido', pk=partido.id_partido)

        # Buscar la inscripción pendiente
        inscripcion = get_object_or_404(
            Inscripcion,
            id=inscripcion_id,
            partido=partido,
            tipo='JUGADOR_PARTIDO',
            estado='PENDIENTE' 
        )

        try:
            # Verificar si todavía hay plazas antes de aceptar 
            if partido.jugadores.count() >= partido.max_jugadores:
                messages.warning(request, f"No se pudo aceptar a {inscripcion.jugador.nombre}: el partido ya está completo.")
                inscripcion.estado = 'RECHAZADA'

                inscripcion.save()

            else:
                inscripcion.estado = 'ACEPTADA'
                inscripcion.save()

                messages.success(request, f"Solicitud de {inscripcion.jugador.nombre} aceptada.")

        except Exception as e:
            messages.error(request, f"Ocurrió un error al aceptar la solicitud: {e}")

        return redirect('detalle_partido', pk=partido.id_partido)


class RechazarInscripcionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs): 
        partido_id = kwargs.get('pk') 
        inscripcion_id = kwargs.get('inscripcion_id') 

        partido = get_object_or_404(Partido, id_partido=partido_id)
        usuario_actual = request.user

        # Verificar si el usuario actual es el creador del partido
        if partido.creador != usuario_actual:
            messages.error(request, "No tienes permiso para rechazar inscripciones en este partido.")
            return redirect('detalle_partido', pk=partido.id_partido)

        # buscar la inscripción pendiente o aceptada para poder rechazarla
        inscripcion = get_object_or_404(
            Inscripcion,
            id=inscripcion_id,
            partido=partido,
            tipo='JUGADOR_PARTIDO'
        )

        # evitar que el creador haga tonterias y se rechace a sí mismo si estuviera en la lista 
        if inscripcion.jugador == usuario_actual:
             messages.warning(request, "No puedes rechazar tu propia inscripción.")
             return redirect('detalle_partido', pk=partido.id_partido)


        try:
            inscripcion.estado = 'RECHAZADA'
            inscripcion.save()
            if partido.jugadores.filter(id=inscripcion.jugador.id).exists():
                 partido.jugadores.remove(inscripcion.jugador)


            messages.success(request, f"Solicitud de {inscripcion.jugador.nombre} rechazada.")

        except Exception as e:
            messages.error(request, f"Ocurrió un error al rechazar la solicitud: {e}")

        return redirect('detalle_partido', pk=partido.id_partido)

class SolicitarUnirseRetoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        partido = get_object_or_404(Partido, pk=kwargs['pk'])
        equipo_id = request.POST.get('equipo_id')
        equipo = get_object_or_404(Equipo, pk=equipo_id, capitan=request.user, tipo_equipo='PERMANENTE')

        if not partido.inscripcion_abierta:
            messages.error(request, "Este reto ya no acepta solicitudes.")
            return redirect('detalle_partido', pk=partido.pk)

        # Comprobar si el equipo ya ha solicitado unirse
        if Inscripcion.objects.filter(partido=partido, equipo=equipo).exists():
            messages.warning(request, f"Tu equipo '{equipo.nombre_equipo}' ya ha solicitado unirse a este reto.")
            return redirect('detalle_partido', pk=partido.pk)

        Inscripcion.objects.create(
            partido=partido,
            equipo=equipo,
            tipo='EQUIPO_PARTIDO',
            estado='PENDIENTE'
        )
        messages.success(request, f"Tu equipo '{equipo.nombre_equipo}' ha solicitado unirse al reto.")
        return redirect('detalle_partido', pk=partido.pk)


class AceptarRetoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        partido = get_object_or_404(Partido, pk=kwargs['pk'])
        inscripcion = get_object_or_404(Inscripcion, pk=kwargs['inscripcion_id'], partido=partido)

        if partido.creador != request.user:
            messages.error(request, "No tienes permiso para gestionar este reto.")
            return redirect('detalle_partido', pk=partido.pk)

        if not partido.esta_esperando_rival:
            messages.error(request, "Este reto ya tiene un rival asignado.")
            return redirect('detalle_partido', pk=partido.pk)

        with transaction.atomic():
            # Asignar equipo visitante y sus jugadores
            partido.equipo_visitante = inscripcion.equipo
            partido.jugadores.add(*inscripcion.equipo.jugadores.all())
            partido.save()

            # Aceptar esta inscripción
            inscripcion.estado = 'ACEPTADA'
            inscripcion.save()

            # Rechazar las demás
            Inscripcion.objects.filter(
                partido=partido,
                tipo='EQUIPO_PARTIDO',
                estado='PENDIENTE'
            ).update(estado='RECHAZADA')

        messages.success(request, f"Has aceptado el reto de '{inscripcion.equipo.nombre_equipo}'. ¡El partido está confirmado!")
        return redirect('detalle_partido', pk=partido.pk)