# bookings/urls.py
from django.urls import path
from .views import RezgoWebhookReceiver

urlpatterns = [
    path('api/webhook/rezgo/', RezgoWebhookReceiver.as_view(), name='rezgo-webhook'),
]