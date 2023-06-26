from django.apps import AppConfig
import os



class TriplexConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'triplex'

    def ready(self):
        run_once = os.environ.get('CMDLINERUNNER_RUN_ONCE') 
        os.environ['CMDLINERUNNER_RUN_ONCE'] = 'True' 
        if run_once is not None:
            return
        from . import cleanup_service
        cleanup_service.start_cleanup_service()