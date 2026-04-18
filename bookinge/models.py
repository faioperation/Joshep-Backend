from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver 
from .utils import sync_to_airtable_generic

class BookingInquiry(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    location = models.CharField(max_length=100)
    event_type = models.CharField(max_length=100)
    group_size = models.CharField(max_length=50)
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=50, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    is_available = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location}"

class RezgoLocation(models.Model):
    city_name = models.CharField(max_length=255) 
    
    rezgo_uid = models.CharField(max_length=100, unique=True) 

    def __str__(self):
        return f"{self.city_name} (ID: {self.rezgo_uid})"

@receiver(post_save, sender=BookingInquiry)
def auto_sync_airtable(sender, instance, created, **kwargs):
    if created:
        print(f"🚀 Signal Triggered for: {instance.name}")
        

        lead_fields = {
            "Name": instance.name,
            "Phone": instance.phone,
            "Email": instance.email,
            "Location": instance.location,
            "Date": str(instance.preferred_date),
            "Time": instance.preferred_time or "Not Set",
            "Status": "Pending"
        }
        
        sync_to_airtable_generic("Leads", lead_fields)

class Venue(models.Model):
    city = models.CharField(max_length=100,null=True)
    category = models.CharField(max_length=50,null=True)  
    venue_name = models.CharField(max_length=255,null=True)
    contact_email = models.EmailField(null=True,blank=True)
    contact_phone = models.CharField(max_length=20 ,null=True)
    priority = models.IntegerField(default=1,null=True)   
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.venue_name} ({self.city})"

class ConfirmedBooking(models.Model):
    booking_id = models.CharField(max_length=50, unique=True)  
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True,blank=True)
    city = models.CharField(max_length=100)
    date = models.DateField()
    time = models.CharField(max_length=50)
    package = models.CharField(max_length=100,null=True,blank=True)
    status = models.CharField(max_length=50, default="Confirmed",)
    
    def __str__(self):
        return f"{self.booking_id} - {self.name}"



