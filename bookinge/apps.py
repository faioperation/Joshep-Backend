from django.apps import AppConfig

class BookingeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookinge'

    def ready(self):
        # এটি জ্যাঙ্গোকে বলে দেয় সার্ভার চালু হওয়ার সময় সিগন্যাল লোড করতে
        import bookinge.models