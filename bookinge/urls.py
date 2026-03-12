from django.urls import path
from .views import process_booking_inquiry

urlpatterns = [
    
    path('inquiry/', process_booking_inquiry, name='process_booking_inquiry'),
]