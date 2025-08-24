import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static


class User(AbstractUser):
    TIPO_GENERO = [
        ('MASCULINO', 'Masculino'),
        ('FEMENINO', 'Femenino'),
        ('NO_ESPECIFICADO', 'Prefiero no decirlo'),
        ('OTRO', 'Otro'),
    ]

    TIPO_POSICION = [
        ('DELANTERO', 'Delantero'),
        ('CENTROCAMPISTA', 'Centrocampista'),
        ('DEFENSA', 'Defensa'),
        ('PORTERO', 'Portero')
    ]
    

    username = models.EmailField(max_length=150, unique=True, verbose_name="email", help_text="Introduce un email válido",)
    nombre = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    genero = models.CharField(max_length=20, choices=TIPO_GENERO, default='NO_ESPECIFICADO', blank=True, null=True)
    
    posicion = models.CharField(max_length=50,choices=TIPO_POSICION, blank=True, null=True)
    partidos_jugados = models.IntegerField(default=0)
    victorias = models.IntegerField(default=0)
    derrotas = models.IntegerField(default=0)
    empates = models.IntegerField(default=0)
     
    calificacion = models.FloatField(default=1000.0)  # ELO

    imagen_perfil = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    banner_perfil = models.ImageField(upload_to='banner_perfil/', blank=True, null=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)



    @property
    def get_avatar_url(self):
        """Devuelve la URL del avatar del usuario o la URL por defecto."""
        if self.imagen_perfil and hasattr(self.imagen_perfil, 'url'):
            return self.imagen_perfil.url
        return static('images/defaults/avatar_default.png')

    @property
    def get_banner_url(self):
        """Devuelve la URL del banner del perfil o la URL por defecto."""
        if self.banner_perfil and hasattr(self.banner_perfil, 'url'):
            return self.banner_perfil.url
        return static('images/defaults/banner_default.png')


    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        #CASO DE QUE USUARIO CAMBIE DE EMAIL POR PERDIDA DE CONTRASEÑA
        if self.pk:  
            originalUser = User.objects.get(pk=self.pk)
            if originalUser.email != self.email:  # si cambia el email
                self.username = self.email  # actualizo el username

        super().save(*args, **kwargs)