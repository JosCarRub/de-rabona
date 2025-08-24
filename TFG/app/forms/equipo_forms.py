from django import forms

from app.models.equipo import Equipo
from django.contrib.auth import get_user_model

from app.models.invitacion import InvitacionEquipo; User = get_user_model()
from django.db.models import Q



class EquipoUpdateForm(forms.ModelForm):
    """
    Formulario para que el capitán de un equipo permanente EDITE sus datos.
    Este formulario NO gestiona la lista de miembros.
    """
    class Meta:
        model = Equipo
        fields = ['nombre_equipo', 'descripcion', 'team_shield', 'team_banner']
        
        widgets = {
            'nombre_equipo': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Nombre de tu escuadra'}),
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Lema, historia, objetivos del equipo...'}),
            'team_shield': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm bg-dark text-white border-secondary'}),
            'team_banner': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm bg-dark text-white border-secondary'}),
        }
        labels = {
            'nombre_equipo': "Nombre del Equipo",
            'descripcion': "Descripción",
            'team_shield': "Escudo del Equipo",
            'team_banner': "Banner del Equipo",
        }
        help_texts = {
            'nombre_equipo': "El nombre debe ser único para equipos permanentes.",
            'descripcion': "Una breve descripción que represente a tu equipo.",
            'team_shield': "Sube una imagen para el escudo (opcional, máx 2MB).",
            'team_banner': "Sube una imagen para el banner de la página del equipo (opcional, máx 5MB).",
        }

    def clean_nombre_equipo(self):
        nombre = self.cleaned_data.get('nombre_equipo')
        query = Equipo.objects.filter(nombre_equipo__iexact=nombre, tipo_equipo='PERMANENTE')
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError("Ya existe un equipo permanente con este nombre.")
        return nombre

    def clean_team_shield(self):
        imagen = self.cleaned_data.get('team_shield')
        if 'team_shield' in self.changed_data and imagen:
            if imagen.size > 2 * 1024 * 1024: 
                raise forms.ValidationError("El escudo no puede superar los 2MB.")
            if not imagen.content_type.startswith('image/'):
                raise forms.ValidationError("El archivo debe ser una imagen válida.")
        return imagen

    def clean_team_banner(self):
        banner = self.cleaned_data.get('team_banner')
        if 'team_banner' in self.changed_data and banner:
            if banner.size > 5 * 1024 * 1024:
                raise forms.ValidationError("El banner no puede superar los 5MB.")
            if not banner.content_type.startswith('image/'):
                raise forms.ValidationError("El archivo debe ser una imagen válida.")
        return banner




class EquipoCreateForm(EquipoUpdateForm): # Hereda de EquipoUpdateForm para no repetir campos
    """
    Formulario para CREAR un equipo permanente. Añade el campo para miembros iniciales.
    """
    miembros_iniciales = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select bg-dark text-white border-secondary', 'size': '8'}),
        required=False,
        label="Añadir Miembros Iniciales (Opcional)",
        help_text="Mantén presionada la tecla Ctrl (o Cmd en Mac) para seleccionar varios."
    )

    class Meta(EquipoUpdateForm.Meta):
        # extends campos del padre y añade el nuevo
        fields = EquipoUpdateForm.Meta.fields + ['miembros_iniciales']

    def __init__(self, *args, **kwargs):
        # este __init__ SÍ espera el argumento 'user'
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # filtro queryset para no mostrar al propio usuario en la lista de miembros a añadir
        if user:
            self.fields['miembros_iniciales'].queryset = User.objects.exclude(pk=user.pk).order_by('nombre')

    def clean_nombre_equipo(self):
        # overrido la validación para que sea más simple en la creación
        nombre = self.cleaned_data.get('nombre_equipo')
        if Equipo.objects.filter(nombre_equipo__iexact=nombre, tipo_equipo='PERMANENTE').exists():
            raise forms.ValidationError("Ya existe un equipo permanente con este nombre.")
        return nombre





class AsignarEquiposForm(forms.Form):
    def __init__(self, *args, **kwargs):
        jugadores_inscritos = kwargs.pop('jugadores_inscritos', None)
        partido = kwargs.pop('partido', None)
        super().__init__(*args, **kwargs)

        EQUIPO_CHOICES = [
            ('', 'Sin Asignar'), 
            ('local', 'Equipo Local'),
            ('visitante', 'Equipo Visitante'),
        ]

        if jugadores_inscritos:
            for jugador in jugadores_inscritos:
                initial_assignment = ''
                if partido and partido.equipo_local and jugador in partido.equipo_local.jugadores.all():
                    initial_assignment = 'local'
                elif partido and partido.equipo_visitante and jugador in partido.equipo_visitante.jugadores.all():
                    initial_assignment = 'visitante'
                

                self.fields[f'jugador_{jugador.id}'] = forms.ChoiceField(
                    choices=EQUIPO_CHOICES,
                    required=False,
                    label=jugador.nombre,
                    initial=initial_assignment,
                    widget=forms.Select(attrs={'class': 'form-select form-select-sm mb-1 d-none player-assignment-select', 'data-jugador-id': jugador.id}) 
                )




class InvitarMiembroForm(forms.Form):
    email = forms.EmailField(
        label="Email del Jugador a Invitar",
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Introduce el email del jugador...'
        })
    )

    def __init__(self, *args, **kwargs):
        self.equipo = kwargs.pop('equipo', None)
        self.invitador = kwargs.pop('invitador', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        try:
            usuario_a_invitar = User.objects.get(username__iexact=email)
        except User.DoesNotExist:
            raise forms.ValidationError("No se encontró ningún usuario con ese email.")

        if usuario_a_invitar == self.invitador:
            raise forms.ValidationError("No puedes invitarte a ti mismo al equipo.")

        if self.equipo and self.equipo.jugadores.filter(pk=usuario_a_invitar.pk).exists():
            raise forms.ValidationError("Este usuario ya es miembro del equipo.")
        
        if InvitacionEquipo.objects.filter(equipo=self.equipo, invitado=usuario_a_invitar, estado='PENDIENTE').exists():
            raise forms.ValidationError("Ya has enviado una invitación a este jugador y está pendiente de respuesta.")
            
        return usuario_a_invitar
    