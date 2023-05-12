from django.apps import AppConfig
import os

class TriplexConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'triplex'

    def ready(self):
        from . import cleanup_service
        cleanup_service.start_cleanup_service()