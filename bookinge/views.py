import json
import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import BookingInquiry, RezgoLocation, Venue
from .utils import check_rezgo_availability, commit_rezgo_booking, sync_to_airtable_generic

# @api_view(['POST'])
# def process_booking_inquiry(request):

#     try:
#         data = request.data
#         user_input = data.get("location") 

#         match = RezgoLocation.objects.filter(city_name__icontains=user_input).first()
#         rezgo_uid = match.rezgo_uid if match else user_input
   
#         inquiry = BookingInquiry.objects.create(
#             name=data.get("name"),
#             email=data.get("email"),
#             location=user_input,
#             preferred_date=data.get("preferred_date"),
#             preferred_time=data.get("preferred_time"),
#         )


#         requested_slot, other_slots = check_rezgo_availability(rezgo_uid, inquiry.preferred_date, inquiry.preferred_time)

        

#         if requested_slot:
#             subject = "Good News! Your Bubble Soccer Slot Is Available"
#             booking_url = requested_slot['booking_url']
#             email_body = f"Hi {inquiry.name},\n\nGreat news! Your slot is available. Book here: {booking_url}\n\nThanks!"
#             inquiry.is_available = True
#             inquiry.save()

         
#         elif other_slots:
#             subject = "Alternative Slots Available"
   
#             limited_slots = other_slots[:5]
#             slots_list = "\n".join([f"- {s['time']}: {s['booking_url']}" for s in limited_slots])
#             email_body = f"Hi {inquiry.name}, unfortunately {inquiry.preferred_time} is full. Try these other times: \n{slots_list}"
            
#         else:
#             subject = "Venue Status Update"
#             email_body = f"Hi {inquiry.name}, we are checking more slots for you."


#         try:
#             # send_mail(subject, email_body, settings.EMAIL_HOST_USER, [inquiry.email], fail_silently=False)
#             print(f"✅ Email successfully sent to {inquiry.email}")
#         except Exception as e:
#             print(f"❌ Mailer Error: {e}")

 
#         sync_to_airtable_generic("Leads", {"Name": inquiry.name, "Email": inquiry.email, "Status": "Processed", "Location": user_input})

#         return Response({"status": "success", "message": "Lead processed and email sent."}, status=201)

#     except Exception as e:
#         print(f"❌ CRITICAL VIEW ERROR: {e}")
#         return Response({"error": str(e)}, status=400)

# AirTable ------------------------------>>><><><><>

@api_view(['POST'])
def process_booking_inquiry(request):
    """ওয়েবসাইট থেকে আসা লিড এয়ারটেবল 'Leads' টেবিলে পাঠাবে।"""
    try:
        data = request.data
        user_input = data.get("location") 

        # ১. ডাটাবেজ থেকে রেজগো আইডি খুঁজে বের করা
        match = RezgoLocation.objects.filter(city_name__icontains=user_input).first()
        rezgo_uid = match.rezgo_uid if match else user_input
   
        # ২. জ্যাঙ্গো ডাটাবেজে সেভ করা
        inquiry = BookingInquiry.objects.create(
            name=data.get("name"),
            email=data.get("email"),
            location=user_input,
            phone=data.get("phone", "N/A"),
            preferred_date=data.get("preferred_date"),
            preferred_time=data.get("preferred_time"),
        )

        # ৩. রেজগো চেক করা
        requested_slot, other_slots = check_rezgo_availability(rezgo_uid, inquiry.preferred_date, inquiry.preferred_time)

        # ৪. ইমেইল বডি তৈরি করা (ইমেইল আপাতত অফ রাখা হয়েছে)
        if requested_slot:
            subject = "Slot Available"
            email_body = "Your slot is ready."
        else:
            subject = "Waitlist"
            email_body = "We are checking more slots."

        # ৫. এয়ারটেবল 'Leads' টেবিলে ডাটা পাঠানো (সঠিক কলাম নাম সহ)
        lead_fields = {
            "Name": inquiry.name,
            "Phone": inquiry.phone,
            "Email": inquiry.email,
            "Location": user_input,      # 'City' এর বদলে 'Location' লিখুন (আপনার এয়ারটেবল অনুযায়ী)
            "Date": str(inquiry.preferred_date), 
            "Time": inquiry.preferred_time or "N/A",
            "Status": "Processed"
        }
        
        print(f"🚀 Syncing Lead to Airtable: {inquiry.name}")
        sync_to_airtable_generic("Leads", lead_fields)

        return Response({"status": "success", "message": "Lead synced to Airtable."}, status=201)

    except Exception as e:
        print(f"❌ View Error: {e}")
        return Response({"error": str(e)}, status=400)



# --------------------------------

@api_view(['POST'])
def voice_booking_handler(request):
    try:
        data = request.data
        user_input = data.get("location")
        match = RezgoLocation.objects.filter(city_name__icontains=user_input).first()
        uid = match.rezgo_uid if match else user_input

        requested_slot, _ = check_rezgo_availability(uid, data['preferred_date'], data['preferred_time'])

        if requested_slot:
            commit_rezgo_booking(data, uid)
            sync_to_airtable_generic("Bookings", {"Booking ID": "AI-V", "Name": data['name'], "Status": "Confirmed"})
            return Response({"status": "success"})
        return Response({"status": "failed"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)