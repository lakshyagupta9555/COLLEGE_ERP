from django.apps import AppConfig


class ErpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'erp'
    
    def ready(self):
        """Import signals when the app is ready"""
        import erp.signals
