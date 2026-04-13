from django.contrib import admin
from .models import BookingInquiry,RezgoLocation,Venue

admin.site.register(BookingInquiry)
admin.site.register(RezgoLocation) 
admin.site.register(Venue) 

