from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from bookinge.models import BookingInquiry, RezgoLocation
from support.models import BusinessFAQ
from .serializers import FAQSerializer, LocationMappingSerializer
from drf_yasg.utils import swagger_auto_schema

# ১. পরিসংখ্যান এপিআই (আগেরটাই আছে) 
class DashboardStatsView(APIView):
    @swagger_auto_schema(
        operation_summary="Get Business Performance Stats",
        operation_description="Returns a real-time overview of total inquiries, confirmed bookings, and AI knowledge status.",
        responses={200: "JSON object containing performance metrics."}
    )
    def get(self, request):
        return Response({
            "total_inquiries": BookingInquiry.objects.count(),
            "confirmed_bookings": BookingInquiry.objects.filter(is_available=True).count(),
            "total_locations": RezgoLocation.objects.count(),
            "total_faqs": BusinessFAQ.objects.count(),
        })

# ২. রেজগো Webhook রিসিভার (আগেরটাই আছে)
class RezgoWebhookReceiver(APIView):
    def post(self, request):
        data = request.data
        return Response({"status": "received"}, status=status.HTTP_200_OK)

# ৩. FAQ Manager (এখান থেকে জোসেফ প্রশ্ন-উত্তর অ্যাড/এডিট করতে পারবে)
class FAQViewSet(viewsets.ModelViewSet):
    """
    Manages the AI Knowledge Base.
    Allows the client to Create, Read, Update, or Delete business rules (e.g. Age limits, rain policy).
    """
    queryset = BusinessFAQ.objects.all()
    serializer_class = FAQSerializer
# ৪. Location Manager (এখান থেকে সিটির রেজগো আইডি সেট করা যাবে)
class LocationMappingViewSet(viewsets.ModelViewSet):
    """
    Handles City-to-Rezgo Mapping.
    Connects website city names to unique Rezgo Item UIDs for accurate automated availability checks.
    """
    queryset = RezgoLocation.objects.all()
    serializer_class = LocationMappingSerializer