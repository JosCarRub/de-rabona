from datetime import timedelta
import uuid
from django.db import models, transaction
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models import F
from django.core.exceptions import ValidationError

from app.models.historial import HistorialELO
from app.models.user import User
from app.models.resultado import Resultado

class Partido(models.Model):
    TIPO_CHOICES = [
        ('SALA', 'Fútbol Sala'),
        ('F7', 'Fútbol 7'),
        ('F11', 'Fútbol 11'),
    ]
    
    MODALIDAD_CHOICES = [
        ('AMISTOSO', 'Amistoso'),
        ('COMPETITIVO', 'Competitivo'),
    ]
    
    NIVEL_CHOICES = [ 
        ('', 'Cualquier nivel'),
        ('PRINCIPIANTE', 'Principiante'),
        ('INTERMEDIO', 'Intermedio'),
        ('AVANZADO', 'Avanzado'),
        ('PRO', 'Profesional/Muy Alto'),
    ]

    ESTADO_CHOICES = [
        ('PROGRAMADO', 'Programado'),
        ('EN_CURSO', 'En curso'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('Bizum', 'Bizum'),
        ('GRATIS', 'Gratuito'),
    ]

    id_partido = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha = models.DateTimeField(verbose_name="Fecha y Hora de Inicio")
    fecha_limite_inscripcion = models.DateTimeField(
        verbose_name="Fecha Límite de Inscripción",
        blank=True, null=True,
        help_text="Hasta cuándo se pueden inscribir los jugadores. Si se deja en blanco, se calculará una hora antes del partido."
    )

    cancha = models.ForeignKey("app.Cancha", on_delete=models.CASCADE, related_name='get_cancha_partido')
    tipo = models.CharField(max_length=4, choices=TIPO_CHOICES)
    nivel = models.CharField(max_length=50, choices=NIVEL_CHOICES, blank=True, null=True)
    modalidad = models.CharField(max_length=11, choices=MODALIDAD_CHOICES, blank=True, null=True)
    max_jugadores = models.PositiveIntegerField(validators=[MinValueValidator(2)], help_text="Número total de jugadores para el partido (ambos equipos).")
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    metodo_pago = models.CharField(max_length=13, choices=METODO_PAGO_CHOICES, blank=True, null=True)
    creador = models.ForeignKey("app.User", on_delete=models.CASCADE, related_name='get_user_creador')
    jugadores = models.ManyToManyField("app.User", related_name='get_jugadores_partido', blank=True)

    equipo_local = models.ForeignKey("app.Equipo", on_delete=models.SET_NULL, null=True, blank=True, related_name='get_equipo_local')
    equipo_visitante = models.ForeignKey("app.Equipo", on_delete=models.SET_NULL, null=True, blank=True, related_name='get_equipo_visitante')

    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PROGRAMADO')
    calificacion_actualizada = models.BooleanField(default=False)
    comentarios = models.TextField(blank=True, null=True)

    @property
    def fecha_fin_calculada(self):
        if self.fecha:
            return self.fecha + timedelta(hours=1)
        return None
    
    @property
    def fecha_limite_inscripcion_efectiva(self):
        if self.fecha_limite_inscripcion:
            return timezone.make_aware(self.fecha_limite_inscripcion) if timezone.is_naive(self.fecha_limite_inscripcion) else self.fecha_limite_inscripcion
        if self.fecha:
            return self.fecha - timedelta(hours=1)
        return None

    @property
    def inscripcion_abierta(self):
        ahora = timezone.now()
        limite = self.fecha_limite_inscripcion_efectiva
        if self.estado != 'PROGRAMADO' or (limite and ahora >= limite):
            return False

        if self.es_reto_de_equipo:
            return self.equipo_visitante is None
        else: # abierto
            if hasattr(self, 'num_jugadores_inscritos'):
                return self.num_jugadores_inscritos < self.max_jugadores
            else:
                return self.jugadores.count() < self.max_jugadores

    @property
    def es_reto_de_equipo(self):
        return self.equipo_local is not None and self.equipo_local.tipo_equipo == 'PERMANENTE'

    @property
    def es_partido_abierto(self):
        return not self.es_reto_de_equipo

    @property
    def esta_esperando_rival(self):
        return self.es_reto_de_equipo and self.equipo_visitante is None

    def save(self, *args, **kwargs):
        if not self.fecha_limite_inscripcion and self.fecha:
            self.fecha_limite_inscripcion = self.fecha - timedelta(hours=1)
        super().save(*args, **kwargs)

    @transaction.atomic
    def actualizar_calificaciones(self):
        if self.calificacion_actualizada or self.modalidad == 'AMISTOSO':
            return
        if not self.equipo_local or not self.equipo_visitante:
            return
        if not hasattr(self, 'get_partido_resultado'):
            return

        K = 32
        resultado = self.get_partido_resultado
        rating_local = self.equipo_local.calificacion_promedio()
        rating_visitante = self.equipo_visitante.calificacion_promedio()

        if resultado.goles_local > resultado.goles_visitante:
            score_local = 1
        elif resultado.goles_local < resultado.goles_visitante:
            score_local = 0
        else:
            score_local = 0.5
        score_visitante = 1 - score_local

        expected_local = 1 / (1 + 10 ** ((rating_visitante - rating_local) / 400))
        expected_visitante = 1 - expected_local

        jugadores_a_actualizar = []
        historial_a_crear = []

        for jugador in self.equipo_local.jugadores.all():
            calificacion_antes = jugador.calificacion
            jugador.calificacion += K * (score_local - expected_local)
            jugadores_a_actualizar.append(jugador)
            historial_a_crear.append(HistorialELO(user=jugador, partido=self, calificacion_antes=calificacion_antes, calificacion_despues=jugador.calificacion))

        for jugador in self.equipo_visitante.jugadores.all():
            calificacion_antes = jugador.calificacion
            jugador.calificacion += K * (score_visitante - expected_visitante)
            jugadores_a_actualizar.append(jugador)
            historial_a_crear.append(HistorialELO(user=jugador, partido=self, calificacion_antes=calificacion_antes, calificacion_despues=jugador.calificacion))

        if jugadores_a_actualizar:
            User.objects.bulk_update(jugadores_a_actualizar, ['calificacion'])
        if historial_a_crear:
            HistorialELO.objects.bulk_create(historial_a_crear)

        self.calificacion_actualizada = True
        self.save(update_fields=['calificacion_actualizada'])

    @transaction.atomic
    def registrar_resultado_y_actualizar_stats(self, goles_local, goles_visitante):
        if self.estado == 'FINALIZADO':
            raise ValidationError("Este partido ya ha sido finalizado.")
        if self.estado == 'CANCELADO':
            raise ValidationError("No se puede registrar resultado para un partido cancelado.")

        Resultado.objects.update_or_create(
            partido=self,
            defaults={'goles_local': goles_local, 'goles_visitante': goles_visitante}
        )
        self.refresh_from_db()

        if self.equipo_local and self.equipo_local.tipo_equipo == 'PERMANENTE':
            self.equipo_local.partidos_jugados_permanente = F('partidos_jugados_permanente') + 1
            if goles_local > goles_visitante:
                self.equipo_local.victorias_permanente = F('victorias_permanente') + 1
            self.equipo_local.save()

        if self.equipo_visitante and self.equipo_visitante.tipo_equipo == 'PERMANENTE':
            self.equipo_visitante.partidos_jugados_permanente = F('partidos_jugados_permanente') + 1
            if goles_visitante > goles_local:
                self.equipo_visitante.victorias_permanente = F('victorias_permanente') + 1
            self.equipo_visitante.save()

        jugadores_del_partido = list(self.jugadores.all())
        jugadores_a_actualizar = []
        
        jugadores_local_ids = set(self.equipo_local.jugadores.values_list('id', flat=True)) if self.equipo_local else set()
        jugadores_visitante_ids = set(self.equipo_visitante.jugadores.values_list('id', flat=True)) if self.equipo_visitante else set()

        for jugador in jugadores_del_partido:
            jugador.partidos_jugados = F('partidos_jugados') + 1
            if jugador.id in jugadores_local_ids:
                if goles_local > goles_visitante:
                    jugador.victorias = F('victorias') + 1
                elif goles_local < goles_visitante:
                    jugador.derrotas = F('derrotas') + 1
                else:
                    jugador.empates = F('empates') + 1
            elif jugador.id in jugadores_visitante_ids:
                if goles_visitante > goles_local:
                    jugador.victorias = F('victorias') + 1
                elif goles_visitante < goles_local:
                    jugador.derrotas = F('derrotas') + 1
                else:
                    jugador.empates = F('empates') + 1
            jugador.save()

        if self.modalidad == 'COMPETITIVO':
            self.actualizar_calificaciones()

        self.estado = 'FINALIZADO'
        self.save(update_fields=['estado'])

    def __str__(self):
        hora_inicio_str = self.fecha.strftime('%d/%m/%Y %H:%M') if self.fecha else "Fecha no definida"
        hora_fin_str = self.fecha_fin_calculada.strftime('%H:%M') if self.fecha_fin_calculada else ""
        nombre_cancha_str = self.cancha.nombre_cancha if self.cancha else "Cancha no definida"
        
        return f"Partido en {nombre_cancha_str} - {hora_inicio_str} a {hora_fin_str}"