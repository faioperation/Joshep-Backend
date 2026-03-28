import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import BookingInquiry, RezgoLocation
from .utils import check_rezgo_availability, commit_rezgo_booking, sync_to_airtable_generic 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    operation_summary="Process Website Inquiries",
    operation_description="Receives data from website, checks Rezgo, sends email, and logs to Airtable Leads.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['name', 'email', 'location', 'preferred_date'],
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
            'email': openapi.Schema(type=openapi.TYPE_STRING, example="john@example.com"),
            'location': openapi.Schema(type=openapi.TYPE_STRING, description="City Name"),
            'preferred_date': openapi.Schema(type=openapi.TYPE_STRING, example="2026-03-15"),
            'preferred_time': openapi.Schema(type=openapi.TYPE_STRING, example="2:00 PM"),
        }
    )
)
@api_view(['POST'])
def process_booking_inquiry(request):
    """ওয়েবসাইট ইনকোয়ারি হ্যান্ডলার (এয়ারটেবল Leads টেবিলে যাবে)"""
    try:
        data = request.data
        city_name = data.get("location")

        # ১. সিটি থেকে আইডি ম্যাপিং
        try:
            location_entry = RezgoLocation.objects.get(city_name=city_name)
            rezgo_uid = location_entry.rezgo_uid
        except RezgoLocation.DoesNotExist:
            rezgo_uid = city_name 

        # ২. ডাটাবেজে ইনকোয়ারি সেভ করা
        inquiry = BookingInquiry.objects.create(
            name=data.get("name"),
            phone=data.get("phone", "N/A"),
            email=data.get("email"),
            location=city_name,
            preferred_date=data.get("preferred_date"),
            preferred_time=data.get("preferred_time"),
        )

        # ৩. রেজগো স্লট চেক
        slot = check_rezgo_availability(rezgo_uid, inquiry.preferred_date, inquiry.preferred_time)

        # ৪. ইমেইল লজিক
        if slot:
            booking_url = f"https://{settings.REZGO_DOMAIN}.rezgo.com/book?item={rezgo_uid}&date={inquiry.preferred_date}"
            subject = "Good News! Your Bubble Soccer Slot Is Available"
            email_body = f"Hi {inquiry.name},\n\nGreat news! We found a slot. Book here: {booking_url}"
            inquiry.is_available = True
            inquiry.save()
        else:
            subject = "Checking Venue Availability"
            email_body = f"Hi {inquiry.name}, we are checking alternative slots for you."

            send_mail(subject, email_body, settings.EMAIL_HOST_USER, [inquiry.email])

        # ৫. এয়ারটেবল 'Leads' টেবিলে ডাটা পাঠানো
        lead_fields = {
            "Name": inquiry.name,
            "Phone": inquiry.phone,
            "Email": inquiry.email,
            "Location": inquiry.location,
            "Date": str(inquiry.preferred_date), # এখানে 'Preferred Date' ছিল, আমি 'Date' করে দিলাম
            "Status": "New Inquiry"
        }
        sync_to_airtable_generic("Leads", lead_fields)

        return Response({"status": "success", "message": "Website inquiry processed and logged to Leads."}, status=201)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)


@swagger_auto_schema(
    method='post',
    operation_summary="Instant Voice AI Booking",
    operation_description="Triggered by Voice AI. Directly commits to Rezgo and logs to Airtable Bookings.",
)
@api_view(['POST'])
def voice_booking_handler(request):
    """ভয়েস এআই বুকিং হ্যান্ডলার (এয়ারটেবল Bookings টেবিলে যাবে)"""
    try:
        data = request.data
        city_name = data.get("location")

        # ১. আইডি ম্যাপিং
        try:
            loc = RezgoLocation.objects.get(city_name=city_name)
            uid = loc.rezgo_uid
        except RezgoLocation.DoesNotExist:
            uid = city_name

        # ২. স্লট চেক করা
        slot = check_rezgo_availability(uid, data['preferred_date'], data['preferred_time'])

        if slot:
            # ৩. সরাসরি রেজগোতে বুকিং কনফার্ম করা
            commit_rezgo_booking(data, uid)
            
            # ৪. এয়ারটেবল 'Bookings' টেবিলে ডাটা পাঠানো
            booking_fields = {
                "Booking ID": "AI-VOICE", # রেজগো রেসপন্স থেকে ট্রানজেকশন আইডি এখানে দিতে পারেন
                "Name": data['name'],
                "Email": data['email'],
                "Phone": data.get('phone', 'N/A'),
                "City": city_name,
                "Date": data['preferred_date'],
                "Time": data['preferred_time'],
                "Status": "Confirmed"
            }
            sync_to_airtable_generic("Bookings", booking_fields)

            # ৫. কনফার্মেশন ইমেইল
            subject = "Booking Confirmed via Voice Assistant"
            email_body = f"Hi {data['name']},\n\nYour booking is confirmed. Please pay deposit at the venue or via the link sent."
            send_mail(subject, email_body, settings.EMAIL_HOST_USER, [data['email']])
            
            return Response({"status": "success", "message": "Booking created and logged to Airtable."})
        else:
            return Response({"status": "failed", "message": "Slot full."}, status=200)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)
    
    
    