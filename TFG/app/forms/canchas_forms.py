from django import forms
from app.models.cancha import Cancha

class CanchasForm(forms.ModelForm):
    class Meta:
        model = Cancha
        fields = [
            'nombre_cancha', 'ubicacion', 'tipo', 'propiedad', 'superficie',
            'costo_partido', 'descripcion', 'disponible', 'imagen'
        ]

        labels = {
            'nombre_cancha': "Nombre de la cancha",
            'ubicacion': "Dirección completa",
            'tipo': "Formato de la cancha (Ej: Fútbol 7)",
            'propiedad': "Tipo de propiedad",
            'superficie': "Superficie de juego",
            'costo_partido': "Costo del Alquiler/Partido (€)",
            'descripcion': "Descripción Adicional",
            'disponible': "Disponible para reservas generales",
            'imagen': "Foto de la cancha (opcional)",
        }

        help_texts = {
            'costo_partido': "Dejar en 0 o vacío si es gratuito.",
            'imagen': "Sube una foto para que los jugadores vean cómo es la cancha.",
        }

        widgets = {
            'nombre_cancha': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'Ej: Polideportivo Municipal La Elipa'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'Ej: Calle Alcalde Garrido, 2, Madrid'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary'
            }),
            'propiedad': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary'
            }),
            'superficie': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary'
            }),
            'costo_partido': forms.NumberInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': '0.00'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'rows': 3,
                'placeholder': 'Añade detalles útiles: cómo llegar, si hay fuentes, etc.'
            }),
            'disponible': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-sm bg-dark text-white border-secondary'
            }),
        }

    def clean_nombre_cancha(self):
        """
        Asegura que no haya otra cancha con el mismo nombre (insensible a mayúsculas/minúsculas).
        """
        nombre = self.cleaned_data.get('nombre_cancha')
        query = Cancha.objects.filter(nombre_cancha__iexact=nombre)
        
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
            
        if query.exists():
            raise forms.ValidationError("Ya existe una cancha con este nombre. Por favor, elige otro.")
        return nombre

    def clean_costo_partido(self):
        """
        Valida que el costo no sea un número negativo.
        """
        costo = self.cleaned_data.get('costo_partido')
        if costo is not None and costo < 0:
            raise forms.ValidationError("El costo no puede ser un número negativo.")
        return costo