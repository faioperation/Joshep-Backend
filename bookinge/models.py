from django.db import models

class BookingInquiry(models.Model):

    EVENT_TYPE_CHOICES = [
        ('Stag Do', 'Stag Do'),
        ('Hen Do', 'Hen Do'),
        ('Birthday Party', 'Birthday Party'),
        ('Corporate Event', 'Corporate Event'),
        ('Kids Party', 'Kids Party'),
        ('School Event', 'School Event'),
        ('Other', 'Other'),
    ]


    GROUP_SIZE_CHOICES = [
        ('10-15 people', '10-15 people'),
        ('16-20 people', '16-20 people'),
        ('21-25 people', '21-25 people'),
        ('26-30 people', '26-30 people'),
        ('30+ people', '30+ people'),
    ]

    LOCATION_CHOICES = [
        ('London', 'London'), ('Manchester', 'Manchester'), ('Birmingham', 'Birmingham'),
        ('Bristol', 'Bristol'), ('Leeds', 'Leeds'), ('Sheffield', 'Sheffield'),
        ('York', 'York'), ('Bradford', 'Bradford'), ('Hull', 'Hull'),
        ('Huddersfield', 'Huddersfield'), ('Halifax', 'Halifax'), ('Wakefield', 'Wakefield'),
        ('Harrogate', 'Harrogate'), ('Scarborough', 'Scarborough'), ('Rotherham', 'Rotherham'),
        ('Doncaster', 'Doncaster'), ('Liverpool', 'Liverpool'), ('Newcastle', 'Newcastle'),
        ('Edinburgh', 'Edinburgh'), ('Glasgow', 'Glasgow'), ('Plymouth', 'Plymouth'),
        ('Exeter', 'Exeter'), ('Bournemouth', 'Bournemouth'), ('Bath', 'Bath'),
        ('Gloucester', 'Gloucester'), ('Swindon', 'Swindon'), ('Weston-super-Mare', 'Weston-super-Mare'),
        ('Yeovil', 'Yeovil'), ('Bridgwater', 'Bridgwater'), ('Taunton', 'Taunton'),
        ('Cardiff', 'Cardiff'), ('Swansea', 'Swansea'), ('Newport', 'Newport'),
        ('Wrexham', 'Wrexham'), ('Barry', 'Barry'), ('Bridgend', 'Bridgend'),
        ('Neath', 'Neath'), ('Port Talbot', 'Port Talbot'), ('Llandudno', 'Llandudno'),
        ('Rhyl', 'Rhyl'), ('Aberystwyth', 'Aberystwyth'), ('Bangor', 'Bangor'),
        ('Nottingham', 'Nottingham'), ('Leicester', 'Leicester'), ('Derby', 'Derby'),
        ('Coventry', 'Coventry'), ('Wolverhampton', 'Wolverhampton'), ('Solihull', 'Solihull'),
        ('West Bromwich', 'West Bromwich'), ('Dudley', 'Dudley'), ('Stoke-on-Trent', 'Stoke-on-Trent'),
        ('Tamworth', 'Tamworth'), ('Loughborough', 'Loughborough'), ('Blackpool', 'Blackpool'),
        ('Wirral', 'Wirral'), ('Preston', 'Preston'), ('Warrington', 'Warrington'),
        ('Wigan', 'Wigan'), ('Bolton', 'Bolton'), ('St Helens', 'St Helens'),
        ('Southport', 'Southport'), ('Blackburn', 'Blackburn'), ('Burnley', 'Burnley'),
        ('Sunderland', 'Sunderland'), ('Middlesbrough', 'Middlesbrough'), ('Hartlepool', 'Hartlepool'),
        ('Stockton-on-Tees', 'Stockton-on-Tees'), ('Durham', 'Durham'), ('Darlington', 'Darlington'),
        ('Gateshead', 'Gateshead'), ('South Shields', 'South Shields'), ('Washington', 'Washington'),
        ('Bishop Auckland', 'Bishop Auckland'), ('Redcar', 'Redcar'),
    ]

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    location = models.CharField(max_length=100, choices=LOCATION_CHOICES)
    event_type = models.CharField(max_length=100, choices=EVENT_TYPE_CHOICES)
    group_size = models.CharField(max_length=50, choices=GROUP_SIZE_CHOICES)

    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=50, blank=True, null=True) # AI চেকিং এর জন্য
    message = models.TextField(blank=True, null=True)

    is_available = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location} ({self.preferred_date})"

    class Meta:
        verbose_name_plural = "Booking Inquiries"

class RezgoLocation(models.Model):
    city_name = models.CharField(max_length=100, unique=True) # : Manchester
    rezgo_uid = models.CharField(max_length=50) # : 419690

    def __str__(self):
        return f"{self.city_name} (ID: {self.rezgo_uid})"