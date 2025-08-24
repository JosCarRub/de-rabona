from django.db import models
import uuid
from django.db.models import Q

class InvitacionEquipo(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADA', 'Aceptada'),
        ('RECHAZADA', 'Rechazada'),
    ]

    id_invitacion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipo = models.ForeignKey('app.Equipo', on_delete=models.CASCADE, related_name='invitaciones')
    invitado_por = models.ForeignKey("app.User", on_delete=models.CASCADE, related_name='invitaciones_enviadas')
    invitado = models.ForeignKey("app.User", on_delete=models.CASCADE, related_name='invitaciones_recibidas')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        #restriccion condiconañl
        constraints = [
            models.UniqueConstraint(
                fields=['equipo', 'invitado'], #la combinación de estos dos campos debe ser única...
                condition=Q(estado='PENDIENTE'), #...solo si la fila cumple esta condición.
                name='unique_pending_invitation_per_user_team'
            )
        ]
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Invitación de {self.invitado_por.nombre} a {self.invitado.nombre} para {self.equipo.nombre_equipo}"