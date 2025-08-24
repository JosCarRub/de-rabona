import os

ENV = os.getenv('DJANGO_ENV', 'production')  # Cambiar esta variable en producción

if ENV == 'production':
    from .production import *
else:
    from .local import *