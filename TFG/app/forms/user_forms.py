from django import forms
from app.models.user import User 
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm




class UserRegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        
        
        self.fields['password1'].label = "Contraseña"
        self.fields['password1'].help_text = "Tu contraseña no puede ser similar a tu información personal."

        
        self.fields['password2'].label = "Confirmación de contraseña"
        self.fields['password2'].help_text = "Introduce la contraseña de nuevo."

        
        self.fields['username'].label = "Correo Electrónico"
        self.fields['nombre'].label = "Nombre Completo"


    class Meta:
        model = get_user_model()
        fields = ( 'username', 'nombre')


    def clean_email(self):
        email = self.cleaned_data.get('username')  
        if email and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('El email introducido ya está registrado, ¡debes introducir otro!')
        return email

class UserUpdateProfilelForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'nombre',
            'fecha_nacimiento', 
            'genero',
            'posicion',
            'ubicacion', 
            'imagen_perfil', 
            'banner_perfil'
        ]

        # Definir etiquetas personalizadas de forma declarativa
        labels = {
            'nombre': "Nombre completo",
            'fecha_nacimiento': "Fecha de nacimiento",
            'genero': "Género",
            'posicion': "Posición de juego preferida",
            'ubicacion': "Ubicación",
            'imagen_perfil': "Foto de perfil",
            'banner_perfil': "Imagen de portada",
        }

        # Definir textos de ayuda
        help_texts = {
            'fecha_nacimiento': "Opcional. Nos ayuda a crear grupos de edad similares.",
            'imagen_perfil': "Sube una foto para tu perfil (opcional).",
            'banner_perfil': "Imagen de portada para personalizar tu perfil (opcional).",
            'ubicacion': "Tu ciudad y provincia para encontrar partidos cerca.",
        }

        # Definir widgets y sus atributos (clases CSS, placeholders, etc.)
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'Tu nombre completo'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control bg-dark text-white border-secondary'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary'
            }),
            'posicion': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'Ciudad, Provincia'
            }),
            'imagen_perfil': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-sm bg-dark text-white border-secondary'
            }),
            'banner_perfil': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-sm bg-dark text-white border-secondary'
            }),
        }

    def clean_nombre(self):
        """
        Valida que el nombre no esté vacío y tenga una longitud mínima.
        """
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip()
            if len(nombre) < 2:
                raise forms.ValidationError("El nombre debe tener al menos 2 caracteres.")
        return nombre

    def clean_imagen_perfil(self):
        """
        Valida el tamaño y formato de la imagen de perfil,
        SOLO SI se ha subido una nueva imagen.
        """
        imagen = self.cleaned_data.get('imagen_perfil')

        # si el campo no ha cambiado, no hacemos nada y devolvemos el valor existente
        if 'imagen_perfil' not in self.changed_data:
            return imagen

        # si el campo ha cambiado, puede ser un archivo nuevo o que se haya limpiado
        # if imagen se encarga del caso en que se marcó clear 
        if imagen:
            # estando aqui, estamos seguros de que imagen es un UploadedFile
            if imagen.size > 5 * 1024 * 1024:
                raise forms.ValidationError("La imagen de perfil no puede superar los 5MB.")
            
            if not imagen.content_type.startswith('image/'):
                raise forms.ValidationError("El archivo debe ser una imagen válida.")
        
        return imagen

    def clean_banner_perfil(self):
        """
        Valida el tamaño y formato de la imagen de banner,
        SOLO SI se ha subido una nueva imagen.
        """
        banner = self.cleaned_data.get('banner_perfil')

        if 'banner_perfil' not in self.changed_data:
            return banner

        if banner:
            if banner.size > 10 * 1024 * 1024:
                raise forms.ValidationError("La imagen de portada no puede superar los 10MB.")
            
            if not banner.content_type.startswith('image/'):
                raise forms.ValidationError("El archivo debe ser una imagen válida.")
        
        return banner