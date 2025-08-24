from django.urls import path




from .views import *

urlpatterns = [


##---------- COMMONS --------------------------------------------------------------------------------------------

    path('', Landing.as_view(), name='landing'),
    path('home', Home.as_view(), name='home'),
    path('info/', InfoEstadoEquipoView.as_view(), name='info'),


    path('dashboard', DashboardAdmin.as_view(), name = 'dashboard'),
    path('dashboard_voice', DashboardAdminVoice.as_view(), name = 'dashboard_voice'),

#---------- REGISTRO --------------------------------------------------------------------------------------------
    path('registro/',UserRegister.as_view(), name='registro' ),

##---------- PERFIL --------------------------------------------------------------------------------------------
    path('perfil/', Perfil.as_view(), name='perfil'),
    path('update_profile',UserUpdateProfile.as_view(), name='update_profile'),
    path('perfil/eliminar/', EliminarCuentaView.as_view(), name='eliminar_cuenta'),

    
##---------- PARTIDOS --------------------------------------------------------------------------------------------
    path('crear_partidos/', CrearPartidos.as_view(), name='crear_partidos'),
    path('buscar_partidos/', BuscarPartidos.as_view(), name='buscar_partidos'),
    path('partido/<uuid:partido_id>/inscribirse/', InscribirsePartidoView.as_view(), name='inscribirse_partido'),
    path('partido/<uuid:pk>/', DetallePartidoView.as_view(), name='detalle_partido'),
    path('partido/<uuid:pk>/registrar_resultado/', RegistrarResultadoPartidoView.as_view(), name='registrar_resultado_partido'),

##---------- INSCRIPCIONES --------------------------------------------------------------------------------------------
path('partido/<uuid:pk>/<uuid:inscripcion_id>/aceptar/', AceptarInscripcionView.as_view(), name='aceptar_inscripcion'),
path('partido/<uuid:pk>/<uuid:inscripcion_id>/rechazar/', RechazarInscripcionView.as_view(), name='rechazar_inscripcion'),

##---------- INSCRIPCIONES (RETOS EQUIPO) --------------------------------------------------------------------------------------------

    path('partido/<uuid:pk>/solicitar_reto/', SolicitarUnirseRetoView.as_view(), name='solicitar_unirse_reto'),
    path('partido/<uuid:pk>/aceptar_reto/<uuid:inscripcion_id>/', AceptarRetoView.as_view(), name='aceptar_reto'),

##---------- CANCHAS --------------------------------------------------------------------------------------------
    path('canchas/', CanchasView.as_view(), name='canchas_lista'), 
    path('canchas/registrar/', RegistrarCanchaView.as_view(), name='canchas_registrar'),
    path('cancha/<uuid:pk_cancha>/', DetalleCanchaView.as_view(), name='detalle_cancha'),


##---------- EQUIPOS --------------------------------------------------------------------------------------------
    path('equipos/crear_equipo_permanente', CrearEquipoPermanenteView.as_view(), name='crear_equipo_permanente'),
    path('equipos/mis_equipos/', MisEquiposListView.as_view(), name='lista_mis_equipos'), 
    path('equipo/<uuid:pk>/', DetalleEquipoView.as_view(), name='detalle_equipo'), 
    path('equipo/<uuid:pk>/editar/', EditarEquipoPermanenteView.as_view(), name='editar_equipo_permanente'),
    path('equipo/<uuid:pk>/abandonar/', AbandonarEquipoView.as_view(), name='abandonar_equipo'),
    path('equipo/<uuid:pk>/eliminar/', EliminarEquipoView.as_view(), name='eliminar_equipo'),


##---------- MIS PARTIDOS --------------------------------------------------------------------------------------------

    path('mis_partidos/', MisPartidosView.as_view(), name='mis_partidos'),

##---------- ESTADISTICAS GENEREALES --------------------------------------------------------------------------------------------

    path('estadisticas/', EstadisticasView.as_view(), name='estadisticas_generales'),

# EQUIPOS----------------
    path('equipo/<uuid:pk>/gestionar-miembros/', GestionarMiembrosView.as_view(), name='gestionar_miembros'),
    
    
##---------- USUARIO / INVITACIONES --------------------------------------------------------------------------------------------

    path('mis-invitaciones/', MisInvitacionesView.as_view(), name='mis_invitaciones'),
    path('invitacion/<uuid:pk>/<str:accion>/', ResponderInvitacionView.as_view(), name='responder_invitacion'),

##----------------------TOGGLE ADMIN CAMBIAR ESTADO EQUIPO---------------------------------------------------------

    path('equipo/<uuid:pk>/toggle-activo/', ToggleActivoEquipoView.as_view(), name='toggle_activo_equipo'),





]