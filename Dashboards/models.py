from django.db import models

class BookingInteraction(models.Model):
    # Progress choices (ড্যাশবোর্ডের Progress কলামের জন্য)
    PROGRESS_STATUS = [
        ('confirmed', 'Confirmed'),
        ('need_staff', 'Need Staff'),
        ('need_attention', 'Need Human Attention'),
        ('pending', 'Pending'),
    ]

    # Booking Type choices (Urgent, New, Existing কলামের জন্য)
    BOOKING_TYPES = [
        ('new', 'New'),
        ('urgent', 'Urgent'),
        ('existing', 'Existing'),
    ]

    # Booking Info / Venue Status (Confirmed/Decline কলামের জন্য)
    VENUE_STATUS = [
        ('confirmed', 'Confirmed'),
        ('decline', 'Decline'),
        ('pending', 'Pending'),
    ]

    # মূল ফিল্ডগুলো (আপনার ড্যাশবোর্ড অনুযায়ী)
    interaction_id = models.CharField(max_length=50, unique=True, verbose_name="Interaction ID") # Rezgo Booking ID
    name = models.CharField(max_length=255)
    email = models.EmailField()
    contact = models.CharField(max_length=20)
    event_date = models.DateField()
    
    assigned_by = models.CharField(max_length=100, default="AI Agent") # Admin, Staff, or AI Agent
    
    progress = models.CharField(
        max_length=50, 
        choices=PROGRESS_STATUS, 
        default='pending'
    )
    
    booking_type = models.CharField(
        max_length=50, 
        choices=BOOKING_TYPES, 
        default='new'
    )
    
    booking_info = models.CharField(
        max_length=50, 
        choices=VENUE_STATUS, 
        default='pending'
    )

    # অতিরিক্ত ডাটা (অটোমেশন এবং AI এর কাজের জন্য)
    venue_name = models.CharField(max_length=255, null=True, blank=True)
    staff_name = models.CharField(max_length=255, null=True, blank=True) # Connecteam থেকে আসবে
    ai_call_summary = models.TextField(null=True, blank=True) # Phone AI এর সামারি রাখার জন্য
    rezgo_raw_data = models.JSONField(null=True, blank=True) # Rezgo থেকে আসা পুরো ডাটা ব্যাকআপ রাখার জন্য
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at'] # নতুন বুকিংগুলো উপরে দেখাবে

    def __str__(self):
        return f"{self.interaction_id} - {self.name}"
    
    
    
