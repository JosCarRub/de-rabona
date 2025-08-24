from app.models.invitacion import InvitacionEquipo


def common_user_info(request):
    context = {}
    if request.user.is_authenticated:
        user = request.user
        context['current_user_nombre'] = user.nombre
        context['current_user_posicion'] = user.get_posicion_display() if user.posicion else "Sin especificar"
        # Ahora simplemente llama a la propiedad del modelo
        context['current_user_avatar_url'] = user.get_avatar_url

        context['invitaciones_pendientes_count'] = InvitacionEquipo.objects.filter(
            invitado=user, 
            estado='PENDIENTE'
        ).count()
    return context