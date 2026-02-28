from django.contrib import admin
from .models import BookingInteraction


@admin.register(BookingInteraction)
class BookingInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'interaction_id',
        'name',
        'email',
        'contact',
        'event_date',
        'booking_type',
        'progress',
        'booking_info',
        'assigned_by',
        'created_at',
    )

    list_filter = (
        'progress',
        'booking_type',
        'booking_info',
        'assigned_by',
        'event_date',
        'created_at',
    )

    search_fields = (
        'interaction_id',
        'name',
        'email',
        'contact',
        'venue_name',
        'staff_name',
    )

    ordering = ('-created_at',)

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ("Booking Information", {
            'fields': (
                'interaction_id',
                'name',
                'email',
                'contact',
                'event_date',
            )
        }),
        ("Status & Assignment", {
            'fields': (
                'booking_type',
                'progress',
                'booking_info',
                'assigned_by',
            )
        }),
        ("Additional Details", {
            'fields': (
                'venue_name',
                'staff_name',
                'ai_call_summary',
                'rezgo_raw_data',
            )
        }),
        ("System Information", {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )
    