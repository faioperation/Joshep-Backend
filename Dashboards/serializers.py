from rest_framework import serializers
from bookinge.models import BookingInquiry, RezgoLocation
from support.models import BusinessFAQ

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessFAQ
        fields = '__all__'

class LocationMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RezgoLocation
        fields = '__all__'