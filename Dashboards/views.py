from django.shortcuts import render

# Create your views here.
# bookings/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import BookingInteraction
from datetime import datetime
from rest_framework import viewsets, views
from rest_framework.response import Response
from .serializers import *
from bookinge.models import BookingInquiry, RezgoLocation
from support.models import BusinessFAQ

class RezgoWebhookReceiver(APIView):
    def post(self, request):
        # Rezgo থেকে আসা ডাটা রিসিভ করা
        data = request.data
        
        try:
            # ১. ডাটা এক্সট্রাক্ট করা (Rezgo-র ফিল্ড অনুযায়ী)
            ref_num = data.get('trans_num') # বুকিং আইডি
            cust_first = data.get('customer_first_name', '')
            cust_last = data.get('customer_last_name', '')
            full_name = f"{cust_first} {cust_last}".strip()
            
            # ইভেন্টের তারিখ (আইটেম লিস্টের প্রথমটা থেকে)
            items = data.get('items', [])
            item_date = items[0].get('item_date') if items else None
            
            # ২. ডাটাবেসে সেভ বা আপডেট করা
            booking_obj, created = BookingInteraction.objects.update_or_create(
                interaction_id=ref_num,
                defaults={
                    'name': full_name,
                    'email': data.get('customer_email'),
                    'contact': data.get('customer_phone'),
                    'event_date': item_date,
                    'booking_type': 'new', # ডিফল্ট নিউ
                    'progress': 'pending', # শুরুতে পেন্ডিং
                    'assigned_by': 'AI Agent',
                    'rezgo_raw_data': data # পুরো ব্যাকআপ রাখা
                }
            )

            if created:
                print(f"New Booking Created: {ref_num}")
            else:
                print(f"Booking Updated: {ref_num}")

            return Response({"status": "success"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({"error": "Failed to process data"}, status=status.HTTP_400_BAD_REQUEST)
    
class DashboardStatsView(views.APIView):
    def get(self, request):
        data = {
            "total_inquiries": BookingInquiry.objects.count(),
            "confirmed_bookings": BookingInquiry.objects.filter(is_available=True).count(),
            "total_locations": RezgoLocation.objects.count(),
            "total_faqs": BusinessFAQ.objects.count(),
        }
        return Response(data)
    
# ২. FAQ Manager (Add/Edit/Delete questions)
class FAQViewSet(viewsets.ModelViewSet):
    queryset = BusinessFAQ.objects.all()
    serializer_class = FAQSerializer
    

# ৩. Location Manager (Manage City names and Rezgo UIDs)
class LocationMappingViewSet(viewsets.ModelViewSet):
    queryset = RezgoLocation.objects.all()
    serializer_class = LocationMappingSerializer