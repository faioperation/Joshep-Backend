from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from bookinge.models import BookingInquiry, RezgoLocation
from support.models import BusinessFAQ
from .serializers import FAQSerializer, LocationMappingSerializer
from drf_yasg.utils import swagger_auto_schema

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

class RezgoWebhookReceiver(APIView):
    def post(self, request):
        data = request.data
        return Response({"status": "received"}, status=status.HTTP_200_OK)

class FAQViewSet(viewsets.ModelViewSet):

    queryset = BusinessFAQ.objects.all()
    serializer_class = FAQSerializer
class LocationMappingViewSet(viewsets.ModelViewSet):

    queryset = RezgoLocation.objects.all()
    serializer_class = LocationMappingSerializer