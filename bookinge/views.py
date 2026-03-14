import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import BookingInquiry, RezgoLocation
from .utils import check_rezgo_availability, commit_rezgo_booking


@csrf_exempt
def process_booking_inquiry(request):
    """
    Handles booking inquiries submitted from the website form.
    This endpoint checks Rezgo availability and sends the booking link via email.
    It does NOT create the booking directly in Rezgo.
    """

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            city_name = data.get("location")

            # Attempt to map the city name to a Rezgo Item UID from the database
            try:
                location_entry = RezgoLocation.objects.get(city_name=city_name)
                rezgo_uid = location_entry.rezgo_uid
            except RezgoLocation.DoesNotExist:
                # If mapping does not exist, use the city name as fallback
                rezgo_uid = city_name 

            # Store the booking inquiry in the database
            inquiry = BookingInquiry.objects.create(
                name=data.get("name"),
                phone=data.get("phone", "N/A"),
                email=data.get("email"),
                location=city_name,
                preferred_date=data.get("preferred_date"),
                preferred_time=data.get("preferred_time"),
            )

            # Check availability using Rezgo Search API
            slot = check_rezgo_availability(
                rezgo_uid,
                inquiry.preferred_date,
                inquiry.preferred_time
            )

            if slot:
                # Generate booking URL for the customer
                booking_url = f"https://{settings.REZGO_DOMAIN}.rezgo.com/book?item={rezgo_uid}&date={inquiry.preferred_date}"

                subject = "Good News! Your Bubble Soccer Slot Is Available"

                email_body = (
                    f"Hi {inquiry.name},\n\n"
                    f"Great news! We found an available slot for your booking.\n"
                    f"Please complete your reservation using the link below:\n\n"
                    f"{booking_url}"
                )

                inquiry.is_available = True
                inquiry.save()

            else:
                subject = "Checking Venue Availability"

                email_body = (
                    f"Hi {inquiry.name},\n\n"
                    f"We are currently checking alternative slots for your requested time."
                    f" Our team will update you shortly."
                )

            # Send response email to the customer
            send_mail(
                subject,
                email_body,
                settings.EMAIL_HOST_USER,
                [inquiry.email]
            )

            return JsonResponse(
                {"status": "success", "message": "Website inquiry processed successfully."},
                status=201
            )

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )


@csrf_exempt
def voice_booking_handler(request):
    """
    Handles booking requests coming from the Voice AI system (Vapi).

    Unlike the website inquiry flow, this endpoint:
    1. Checks availability
    2. Directly commits the booking to Rezgo
    3. Sends a confirmation email to the customer
    """

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            city_name = data.get("location")

            # Convert city name into Rezgo Item UID using database mapping
            try:
                loc = RezgoLocation.objects.get(city_name=city_name)
                uid = loc.rezgo_uid
            except:
                # Fallback: treat city name as UID
                uid = city_name

            # Check slot availability
            slot = check_rezgo_availability(
                uid,
                data['preferred_date'],
                data['preferred_time']
            )

            if slot:
                # Directly create booking in Rezgo
                commit_rezgo_booking(data, uid)

                subject = "Booking Confirmed via Voice Assistant"

                booking_url = f"https://{settings.REZGO_DOMAIN}.rezgo.com/book?item={uid}&date={data['preferred_date']}"

                email_body = (
                    f"Hi {data['name']},\n\n"
                    f"Your booking has been successfully created through our AI Voice Assistant.\n\n"
                    f"Please complete the deposit payment using the link below:\n"
                    f"{booking_url}"
                )

                # Send confirmation email
                send_mail(
                    subject,
                    email_body,
                    settings.EMAIL_HOST_USER,
                    [data['email']]
                )

                return JsonResponse(
                    {"status": "success", "message": "Booking successfully created in Rezgo."}
                )

            else:
                return JsonResponse(
                    {"status": "failed", "message": "Requested slot is fully booked."}
                )

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )