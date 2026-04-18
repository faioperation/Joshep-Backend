from django.db import models

class BookingInteraction(models.Model):

    PROGRESS_STATUS = [
        ('confirmed', 'Confirmed'),
        ('need_staff', 'Need Staff'),
        ('need_attention', 'Need Human Attention'),
        ('pending', 'Pending'),
    ]

    BOOKING_TYPES = [
        ('new', 'New'),
        ('urgent', 'Urgent'),
        ('existing', 'Existing'),
    ]

    VENUE_STATUS = [
        ('confirmed', 'Confirmed'),
        ('decline', 'Decline'),
        ('pending', 'Pending'),
    ]

    interaction_id = models.CharField(max_length=50, unique=True, verbose_name="Interaction ID")
    name = models.CharField(max_length=255)
    email = models.EmailField()
    contact = models.CharField(max_length=20)
    event_date = models.DateField()
    
    assigned_by = models.CharField(max_length=100, default="AI Agent")
    
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

    venue_name = models.CharField(max_length=255, null=True, blank=True)
    staff_name = models.CharField(max_length=255, null=True, blank=True)
    ai_call_summary = models.TextField(null=True, blank=True)
    rezgo_raw_data = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.interaction_id} - {self.name}"