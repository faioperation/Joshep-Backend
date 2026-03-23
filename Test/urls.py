from django.urls import path
from .views import whatsapp_webhook

urlpatterns = [
    path('webhook/', whatsapp_webhook, name='whatsapp_webhook'), # শেষে স্ল্যাশ (/) আছে কিনা দেখুন
]

