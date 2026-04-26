import json
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from bookinge.models import BookingInquiry, RezgoLocation
from support.models import BusinessFAQ
from .serializers import FAQSerializer, LocationMappingSerializer
from rest_framework import viewsets
from rest_framework.views import APIView

class DashboardStatsView(APIView):
    def get(self, request):
        return Response({
            "total_inquiries": BookingInquiry.objects.count(),
            "confirmed_bookings": BookingInquiry.objects.filter(is_available=True).count(),
            "total_locations": RezgoLocation.objects.count(),
            "total_faqs": BusinessFAQ.objects.count(),
        })

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def rezgo_webhook_receiver(request):
    print("\n" + "="*50)
    print("🚀 WEBHOOK HIT DETECTED FROM REZGO")
    
    try:
        data = request.data
        if not data:
            data = json.loads(request.body.decode('utf-8'))

        print("DEBUG: Raw Webhook Data ->", json.dumps(data, indent=2))

        booking_id = str(data.get('trans_num') or data.get('booking_id', 'N/A'))
        first_name = data.get('customer_first_name') or data.get('first_name', '')
        last_name = data.get('customer_last_name') or data.get('last_name', '')
        email = data.get('customer_email') or data.get('email', '')
        phone = data.get('customer_phone') or data.get('phone', '')

        booking_data = {
            "Booking ID": booking_id,
            "Name": f"{first_name} {last_name}".strip() or "Guest Customer",
            "Email": email,
            "Phone": phone,
            "Status": "Confirmed"
        }

        from bookinge.utils import sync_to_airtable_generic
        success = sync_to_airtable_generic("Bookings", booking_data)

        if success:
            print(f"✅ Webhook Success: Booking {booking_id} synced to Airtable.")
            return Response({"status": "success"}, status=200)
        else:
            print(f"❌ Webhook Failed: Could not sync to Airtable.")
            return Response({"status": "airtable_error"}, status=200)

    except Exception as e:
        print(f"❌ Webhook Critical Error: {e}")
        return Response({"error": str(e)}, status=200)

class FAQViewSet(viewsets.ModelViewSet):
    queryset = BusinessFAQ.objects.all()
    serializer_class = FAQSerializer

class LocationMappingViewSet(viewsets.ModelViewSet):
    queryset = RezgoLocation.objects.all()
    serializer_class = LocationMappingSerializer