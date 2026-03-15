from django.urls import path
from .views import process_booking_inquiry, voice_booking_handler

urlpatterns = [
    # 1. URL endpoint for website booking inquiries
    path("inquiry/", process_booking_inquiry, name="web_inquiry"),
    # 2. URL endpoint used by the Voice AI system (Vapi) for automatic bookings
    path("voice-booking/", voice_booking_handler, name="voice_booking"),
]



