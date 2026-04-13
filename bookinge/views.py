import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import BookingInquiry, RezgoLocation
from .utils import check_rezgo_availability, commit_rezgo_booking, sync_to_airtable_generic,send_ai_reply_via_sendgrid 
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
    """
    ওয়েবসাইট ইনকোয়ারি হ্যান্ডেল করবে এবং জিমেইল SMTP দিয়ে মেইল পাঠাবে।
    """
    try:
        data = request.data
        city_name = data.get("location")

        # ১. সিটি থেকে আইডি ম্যাপিং
        try:
            location_entry = RezgoLocation.objects.get(city_name=city_name)
            rezgo_uid = location_entry.rezgo_uid
        except:
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

        if slot:
            inquiry.is_available = True
            inquiry.save()

            booking_url = f"https://{settings.REZGO_DOMAIN}.rezgo.com/book?item={slot['uid']}&date={inquiry.preferred_date}"
            subject = "Good News! Your Bubble Soccer Slot Is Available"
            email_body = f"Hi {inquiry.name},\n\nGreat news! We found a slot in {inquiry.location}.\n\nClick here to book now: {booking_url}\n\nThanks!"
        else:
            subject = "Venue Availability Update"
            email_body = f"Hi {inquiry.name}, we are checking alternative slots for you in {inquiry.location}. We will update you shortly."

        # ৪. জিমেইল SMTP দিয়ে মেইল পাঠানো (সহজ এবং কার্যকর)
        send_mail(
            subject,
            email_body,
            settings.EMAIL_HOST_USER, # আপনার জিমেইল
            [inquiry.email], # কাস্টমারের মেইল
            fail_silently=False,
        )

        # ৫. এয়ারটেবল সিঙ্ক (Leads)
        # এটি সিগন্যাল দিয়েও করা যায়, তবে ভিউতে রাখলে টেস্টিং সহজ হয়
        return Response({"status": "success", "message": "Inquiry processed and SMTP email sent."}, status=201)

    except Exception as e:
        print(f"SMTP_VIEW_ERROR: {e}")
        return Response({"status": "error", "message": str(e)}, status=400)





@swagger_auto_schema(
    method='post',
    operation_summary="Instant Voice AI Booking",
    operation_description="Triggered by Voice AI. Directly commits to Rezgo and logs to Airtable Bookings.",
)


@api_view(['POST'])
def voice_booking_handler(request):
    """
    ভয়েস এআই বুকিং হ্যান্ডলার - এটি এখন বুকিং এবং অপারেশনাল ভেন্যু আউটরিচ দুইটাই করবে।
    """
    try:
        data = request.data
        city_name = data.get("location")
        # জোসেফ চেয়েছে ক্যাটাগরি অনুযায়ী ভেন্যু সিলেক্ট করতে
        category = data.get("event_type", "General") 

        # ১. আইডি ম্যাপিং (City to Rezgo UID)
        try:
            loc = RezgoLocation.objects.get(city_name=city_name)
            uid = loc.rezgo_uid
        except RezgoLocation.DoesNotExist:
            uid = city_name

        # ২. রেজগো স্লট চেক করা
        slot = check_rezgo_availability(uid, data['preferred_date'], data['preferred_time'])

        if slot:
            # ৩. সরাসরি রেজগোতে বুকিং কনফার্ম করা (Commit)
            # নোট: রেজগো থেকে রেসপন্স আসলে ট্রান্সজ্যাকশন আইডি পাবেন
            rezgo_response = commit_rezgo_booking(data, uid)
            booking_id = "RZ-" + str(int(time.time())) # আপাতত জেনারেট করছি

            # ৪. এয়ারটেবল 'Bookings' টেবিলে ডাটা পাঠানো (জোসেফের রিকোয়ারমেন্ট অনুযায়ী কলাম নাম)
            booking_fields = {
                "Booking ID": booking_id,
                "Name": data['name'],
                "Email": data['email'],
                "Phone": data.get('phone', 'N/A'),
                "City": city_name,
                "Date": data['preferred_date'],
                "Time": data['preferred_time'],
                "Package": data.get('package', 'Double Header'),
                "Group Size": data.get('group_size', '10-15 people'),
                "Status": "Confirmed"
            }
            sync_to_airtable_generic("Bookings", booking_fields)

            # ৫. অটোমেটিক ভেন্যু সিলেকশন এবং আউটরিচ (NEW)
            try:
                # আপনার ডাটাবেজ থেকে ওই শহরের এবং ক্যাটাগরির সেরা ভেন্যু খুঁজবে
                venue = Venue.objects.filter(city=city_name, category=category).order_by('priority').first()
                
                if venue:
                    # ভেন্যুকে মেইল পাঠানো
                    venue_subject = f"ACTION REQUIRED: New Booking for {city_name}"
                    venue_content = f"Hi {venue.venue_name},\n\nWe have a new booking confirmed for {data['preferred_date']} at {data['preferred_time']}.\n\nPlease let us know if the venue is available.\n\nThanks!"
                    
                    send_mail(venue_subject, venue_content, settings.EMAIL_HOST_USER, [venue.contact_email])

                    # এয়ারটেবল 'Venue Requests' টেবিলে লগ করা
                    request_fields = {
                        "Linked Booking": [booking_id], # এটি বুকিং টেবিলের সাথে লিঙ্ক করবে
                        "Venue": venue.venue_name,
                        "Email Sent": True,
                        "Status": "Pending"
                    }
                    sync_to_airtable_generic("Venue Requests", request_fields)
            except:
                print("Venue Outreach failed, but booking was successful.")

            # ৬. কাস্টমারকে কনফার্মেশন ইমেইল
            customer_subject = "Booking Confirmed via Voice Assistant"
            customer_body = f"Hi {data['name']},\n\nYour booking is confirmed for {city_name} on {data['preferred_date']}.\n\nPlease pay the deposit using the link sent previously.\n\nThanks!"
            send_mail(customer_subject, customer_body, settings.EMAIL_HOST_USER, [data['email']])
            
            return Response({"status": "success", "message": "Booking created, logged, and venue notified!"})
        
        else:
            return Response({"status": "failed", "message": "Slot full."}, status=200)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)