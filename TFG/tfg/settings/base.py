from pathlib import Path
import os
from django.urls import reverse_lazy
from dotenv import load_dotenv
import dj_database_url

# 1. DEFINICIÓN DEL DIRECTORIO BASE
# ----------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 2. CARGA DE VARIABLES DE ENTORNO
# ---------------------------------
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 3. CONFIGURACIONES DE SEGURIDAD
# -------------------------------
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = True
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# 4. APLICACIONES INSTALADAS
# --------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'crispy_forms',
    'crispy_bootstrap5',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# 5. MIDDLEWARE
# -------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 6. CONFIGURACIÓN DE URLS Y APLICACIÓN
# -------------------------------------
ROOT_URLCONF = 'tfg.urls'
WSGI_APPLICATION = 'tfg.wsgi.application'

# 7. CONFIGURACIÓN DE LA BASE DE DATOS (LA PARTE CLAVE)
# ---------------------------------------------------
# `dj_database_url.config()` lee la variable `DATABASE_URL` del .env 
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
    )
}

# 8. CONFIGURACIÓN DE PLANTILLAS (TEMPLATES)
# ------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.common_user_info', 
            ],
        },
    },
]

# 9. VALIDACIÓN DE CONTRASEÑAS
# ----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 10. INTERNACIONALIZACIÓN
# ------------------------
LANGUAGE_CODE = 'es-es' 
TIME_ZONE = 'Europe/Madrid' 
USE_I18N = True
USE_TZ = True

# 11. ARCHIVOS ESTÁTICOS Y MEDIA
# ------------------------------
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app', 'static'),
]


PRIVATE_MEDIA_URL = 'private-media/'
PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, 'private_media')




# 12. CONFIGURACIÓN DE AUTENTICACIÓN
# ----------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'app.User'
LOGIN_REDIRECT_URL = ('home')
LOGOUT_REDIRECT_URL = reverse_lazy('landing')


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


AI_AGENT_INTERNAL_URL = os.environ.get('AI_AGENT_INTERNAL_URL')

AGENT_SECRET_KEY = os.environ.get('AGENT_SECRET_KEY')
