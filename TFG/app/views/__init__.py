from .canchas_views import CanchasView, RegistrarCanchaView, DetalleCanchaView
from .commons_views import Landing, Home, DashboardAdmin, DashboardAdminVoice, InfoEstadoEquipoView
from .partido_views import CrearPartidos, BuscarPartidos,DetallePartidoView, InscribirsePartidoView, RegistrarResultadoPartidoView, RechazarInscripcionView, AceptarInscripcionView, SolicitarUnirseRetoView, AceptarRetoView
from .user_views import UserRegister,Perfil, UserUpdateProfile, MisInvitacionesView, ResponderInvitacionView, EliminarCuentaView
from .equipo_views import CrearEquipoPermanenteView, MisEquiposListView, DetalleEquipoView, EditarEquipoPermanenteView, GestionarMiembrosView, AbandonarEquipoView, EliminarEquipoView, ToggleActivoEquipoView
from .estadisticas_views import EstadisticasView
from .mis_partidos_views import MisPartidosView



__all__ = [
    "CanchasView",
    "RegistrarCanchaView",
    "DetalleCanchaView",
    "Landing",
    "Home",

    
    "CrearPartidos",
    "BuscarPartidos",
    "DetallePartidoView",
    "InscribirsePartidoView",
    "RegistrarResultadoPartidoView",
    "AceptarInscripcionView", 
    "RechazarInscripcionView",
    "SolicitarUnirseRetoView",
    "AceptarRetoView",
    "EliminarCuentaView",

    "UserRegister",
    "Perfil",
    "UserUpdateProfile",
    "CrearEquipoPermanenteView",
    "MisEquiposListView",
    "DetalleEquipoView",
    "EditarEquipoPermanenteView",
    "AbandonarEquipoView",
    "EliminarEquipoView",
    "ToggleActivoEquipoView",
    "MisPartidosView",
    "EstadisticasView",
    "GestionarMiembrosView",
    "ResponderInvitacionView",
    "MisInvitacionesView",
    "InfoEstadoEquipoView",
















    "DashboardAdmin",
    "DashboardAdminVoice",
]
