import json
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import BookingInquiry, RezgoLocation
from .utils import check_rezgo_availability, commit_rezgo_booking
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
@swagger_auto_schema(
    method='post',
    operation_summary="Process Website Inquiries",
    operation_description="Receives data from the website form, checks Rezgo availability, and sends a booking link via email.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['name', 'email', 'location', 'preferred_date'],
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
            'email': openapi.Schema(type=openapi.TYPE_STRING, example="john@example.com"),
            'location': openapi.Schema(type=openapi.TYPE_STRING, description="City Name (mapped to Rezgo UID)"),
            'preferred_date': openapi.Schema(type=openapi.TYPE_STRING, example="2026-03-15"),
            'preferred_time': openapi.Schema(type=openapi.TYPE_STRING, example="2:00 PM"),
        }
    )
)
@api_view(['POST'])
def process_booking_inquiry(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            city_name = data.get("location")

            # সিটি থেকে আইডি ম্যাপিং
            try:
                location_entry = RezgoLocation.objects.get(city_name=city_name)
                rezgo_uid = location_entry.rezgo_uid
            except:
                rezgo_uid = city_name # Fallback

            inquiry = BookingInquiry.objects.create(
                name=data.get("name"),
                phone=data.get("phone", "N/A"),
                email=data.get("email"),
                location=city_name,
                preferred_date=data.get("preferred_date"),
                preferred_time=data.get("preferred_time"),
            )

            slot = check_rezgo_availability(rezgo_uid, inquiry.preferred_date, inquiry.preferred_time)

            if slot:
                booking_url = f"https://{settings.REZGO_DOMAIN}.rezgo.com/book?item={rezgo_uid}&date={inquiry.preferred_date}"
                subject = "Bubble Soccer Slot Available!"
                email_body = f"Hi {inquiry.name}, We found a slot. Book here: {booking_url}"
                inquiry.is_available = True
                inquiry.save()
            else:
                subject = "Booking Update"
                email_body = f"Hi {inquiry.name}, requested slot is full. We'll update you."

            send_mail(subject, email_body, settings.EMAIL_HOST_USER, [inquiry.email])
            return JsonResponse({"status": "success", "message": "Website inquiry processed."}, status=201)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

@swagger_auto_schema(
    method='post',
    operation_summary="Instant Voice AI Booking",
    operation_description="Triggered by the Voice AI Assistant during a phone call. Directly blocks a slot in Rezgo and sends confirmation.",
)
@api_view(['POST'])
def voice_booking_handler(request):
    """ভয়েস এআই সরাসরি এখানে ডাটা পাঠাবে"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            city_name = data.get("location")
            # আইডি ম্যাপিং
            try:
                loc = RezgoLocation.objects.get(city_name=city_name)
                uid = loc.rezgo_uid
            except: uid = city_name

            slot = check_rezgo_availability(uid, data['preferred_date'], data['preferred_time'])

            if slot:
                commit_rezgo_booking(data, uid) # সরাসরি বুকিং হবে
                return JsonResponse({"status": "success", "message": "Voice booking created in Rezgo."})
            else:
                return JsonResponse({"status": "failed", "message": "Slot full."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)