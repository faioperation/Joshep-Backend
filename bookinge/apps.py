from django.apps import AppConfig

class BookingeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookinge'

    def ready(self):
        import bookinge.models # এটি নিশ্চিত করবে যে সিগন্যাল কাজ করবে