import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import BookingInquiry, RezgoLocation  # Import the required models
from .utils import check_rezgo_availability


@csrf_exempt
def process_booking_inquiry(request):
    """
    View to receive booking inquiries from the Frontend or Postman.
    This function automatically finds the corresponding Rezgo UID based on the city name.
    """

    if request.method == "POST":
        try:
            # 1. Receive data sent from the frontend
            data = json.loads(request.body)
            city_name = data.get("location")  # Example: user sends "Manchester"

            # 2. Smart logic to find the Rezgo UID using the city name
            try:
                # Check the mapping saved in the Django Admin Panel
                location_entry = RezgoLocation.objects.get(city_name=city_name)
                rezgo_search_param = location_entry.rezgo_uid  # Example: "419690"

            except RezgoLocation.DoesNotExist:
                # If the city is not found in the database,
                # temporarily search using the city name itself (Fallback method)
                rezgo_search_param = city_name

            # 3. Save the user's main inquiry in the database
            inquiry = BookingInquiry.objects.create(
                name=data.get("name"),
                phone=data.get("phone"),
                email=data.get("email"),
                location=city_name,  # Store the city name in the database
                event_type=data.get("event_type"),
                group_size=data.get("group_size"),
                preferred_date=data.get("preferred_date"),
                preferred_time=data.get("preferred_time"),
                message=data.get("message", ""),
            )

            # 4. Check availability using the Rezgo API
            # The UID (or fallback search parameter) is sent to the API
            available_slots = check_rezgo_availability(
                rezgo_search_param,
                data.get("preferred_date"),
                inquiry.preferred_time
            )

            # 5. Email and response logic
            if available_slots:
                # If a slot is available
                inquiry.is_available = True
                inquiry.save()

                slot = available_slots[0]
                subject = f"Good News! Your {slot['time']} slot is available"

                email_body = f"""
Hi {inquiry.name},

Great news! We have confirmed that the {slot['time']} slot on {inquiry.preferred_date} is available in {inquiry.location}.

To secure this booking, please click the link below to pay your £49 deposit:
{slot['booking_url']}

If you have any further questions, simply reply to this email.

Thanks,
Spartacus Bubble Soccer Team
                """

            else:
                # If no slot is available
                subject = "Update regarding your Bubble Soccer Inquiry"

                email_body = f"""
Hi {inquiry.name},

Thank you for your inquiry. We are currently checking the availability for your requested time ({inquiry.preferred_time}) in {inquiry.location} on {inquiry.preferred_date}.

Our team will get back to you within a a few hours with a confirmation or alternative slots.

Thanks for your patience!
Spartacus Bubble Soccer Team
                """

            # 6. Send email using Django email settings
            send_mail(
                subject,
                email_body,
                settings.EMAIL_HOST_USER,
                [inquiry.email],
                fail_silently=False
            )

            return JsonResponse(
                {
                    "status": "success",
                    "available": inquiry.is_available,
                    "message": "Inquiry processed and email sent successfully.",
                },
                status=201,
            )

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400
            )

    return JsonResponse(
        {"status": "error", "message": "Only POST requests are allowed"},
        status=405
    )