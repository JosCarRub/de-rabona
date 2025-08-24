from datetime import datetime, time, timedelta
from django import forms
from app.models.cancha import Cancha
from app.models.equipo import Equipo
from app.models.partido import Partido
from django.db.models import Q


from django.utils import timezone as django_timezone
from django.utils.timezone import make_aware


# PartidoForm && ResultadoPartidoForm


class PartidoForm(forms.ModelForm):
    dia_partido = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control bg-dark text-white border-secondary'}),
        label="Día del Partido"
    )
    HORARIOS_CHOICES = [(time(h, 0).strftime('%H:%M'), f"{h:02d}:00") for h in range(10, 23)]
    hora_inicio_partido = forms.ChoiceField(
        choices=HORARIOS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
        label="Hora de Inicio"
    )

    equipo_local = forms.ModelChoiceField(
        queryset=Equipo.objects.none(),
        required=False,
        label="Tu Equipo (Opcional - para crear un reto)",
        widget=forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
        help_text="Si seleccionas uno de tus equipos, crearás un 'Reto de Equipo'. Si lo dejas en blanco, crearás un 'Partido Abierto' para jugadores individuales."
    )

    class Meta:
        model = Partido
        fields = [
            'equipo_local', 'cancha', 'tipo', 'nivel', 'modalidad',
            'max_jugadores', 'costo', 'metodo_pago', 'comentarios'
        ]
        widgets = {
            'cancha': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'tipo': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'nivel': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'modalidad': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'max_jugadores': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
            'comentarios': forms.Textarea(attrs={'rows': 3, 'class': 'form-control bg-dark text-white border-secondary'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['equipo_local'].queryset = Equipo.objects.filter(
                capitan=self.user,
                tipo_equipo='PERMANENTE',
                activo=True
            ).distinct().order_by('nombre_equipo')
            self.fields['equipo_local'].empty_label = "(Crear Partido Abierto)"

    def clean(self):
        cleaned_data = super().clean()
        dia = cleaned_data.get('dia_partido')
        hora_str = cleaned_data.get('hora_inicio_partido')
        cancha = cleaned_data.get('cancha')
        costo = cleaned_data.get("costo")
        metodo_pago = cleaned_data.get("metodo_pago")

        #  fecha y hora
        if dia and hora_str:
            try:
                hora_obj = datetime.strptime(hora_str, '%H:%M').time()
                naive_datetime = datetime.combine(dia, hora_obj)
                fecha_inicio = make_aware(naive_datetime)
                if fecha_inicio < django_timezone.now():
                    self.add_error('dia_partido', 'La fecha y hora de inicio no puede ser en el pasado.')
                else:
                    cleaned_data['fecha'] = fecha_inicio
            except ValueError:
                self.add_error('hora_inicio_partido', "Formato de hora inválido.")
        
        #solapamiento de canchas 
        if cancha and 'fecha' in cleaned_data:
            fecha_inicio = cleaned_data['fecha']
            fecha_fin_propuesta = fecha_inicio + timedelta(hours=1)
            
            partidos_conflictivos_query = Partido.objects.filter(
                cancha=cancha,
                estado__in=['PROGRAMADO', 'EN_CURSO'],
                fecha__lt=fecha_fin_propuesta,
                fecha__gt=fecha_inicio - timedelta(hours=1)
            )

            if self.instance and self.instance.pk:
                partidos_conflictivos_query = partidos_conflictivos_query.exclude(pk=self.instance.pk)
            
            if partidos_conflictivos_query.exists():
                self.add_error('hora_inicio_partido', forms.ValidationError(
                    f"La cancha '{cancha.nombre_cancha}' ya está reservada en ese horario.",
                    code='solapamiento'
                ))
                self.add_error('cancha', "Horario no disponible.")

        # costo y método de pago 
        if costo is not None:
            if costo > 0 and metodo_pago == 'GRATIS':
                self.add_error('metodo_pago', 'Si el partido tiene un costo, el método de pago no puede ser "Gratis".')
            elif costo == 0 and metodo_pago != 'GRATIS' and metodo_pago is not None:
                cleaned_data['metodo_pago'] = 'GRATIS'
        elif metodo_pago != 'GRATIS' and metodo_pago is not None:
            self.add_error('costo', 'Debes especificar un costo o seleccionar "Gratis" como método de pago.')

        return cleaned_data





class ResultadoPartidoForm(forms.Form):
    goles_local = forms.IntegerField(
        label="Goles del Equipo Local",
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': '0'})
    )
    goles_visitante = forms.IntegerField(
        label="Goles del Equipo Visitante",
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': '0'})
    )