import requests
import json
import time
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Content
from urllib.parse import quote  


def check_rezgo_availability(location_or_sku, date_string, preferred_time=None):

    params = {
        'transcode': settings.REZGO_CID,
        'key': settings.REZGO_API_KEY,
        'i': 'search',
        'q': location_or_sku
    }
    try:
        response = requests.get("https://api.rezgo.com/json", params=params)
        data = response.json()
        
        unique_slots = {} 
        requested_slot = None

        if int(data.get('total', 0)) > 0:
            items = data.get('item', [])
            if isinstance(items, dict): items = [items]
            
            for item in items:
                item_time = item.get('time', '').strip()
                item_sku = item.get('com') 
                
                encoded_time = quote(item_time)
                
                booking_url = f"https://{settings.REZGO_DOMAIN}.rezgo.com/book?com={item_sku}&date={date_string}&time={encoded_time}&q=8"

                slot_info = {
                    'time': item_time,
                    'booking_url': booking_url,
                    'sku': item_sku
                }

                if item_time not in unique_slots:
                    unique_slots[item_time] = slot_info

                if preferred_time:
                    u_time_clean = preferred_time.strip().lower().replace(" ", "").lstrip('0')
                    i_time_clean = item_time.lower().replace(" ", "").lstrip('0')
                    if u_time_clean == i_time_clean:
                        requested_slot = slot_info

                
        return requested_slot, list(unique_slots.values())

    except Exception as e:
        print(f"❌ UTILS_ERROR: {e}")
        return None, []


def commit_rezgo_booking(data, item_uid):
    URL = "https://api.rezgo.com/xml"
    ref_id = f"VOICE-{int(time.time())}"
    xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <request>
        <transcode>{settings.REZGO_CID}</transcode>
        <key>{settings.REZGO_API_KEY}</key>
        <instruction>commit</instruction>
        <booking>
            <date>{data['preferred_date']}</date>
            <book>{item_uid}</book>
            <adult_num>1</adult_num>
        </booking>
        <payment>
            <tour_first_name>{data['name']}</tour_first_name>
            <tour_last_name>AI Assistant</tour_last_name>
            <tour_email_address>{data['email']}</tour_email_address>
            <payment_method>Cash</payment_method>
            <agree_terms>1</agree_terms>
            <status>1</status>
            <refid>{ref_id}</refid>
        </payment>
    </request>"""
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(URL, data=xml_payload, headers=headers)
        return response.text
    except:
        return None


def sync_to_airtable_generic(table_name, fields):
    
    print(f"--- AIRTABLE SYNC STARTING ---")
    api_key = settings.AIRTABLE_API_KEY
    base_id = settings.AIRTABLE_BASE_ID
    print(f"DEBUG: Table -> {table_name}")
    print(f"DEBUG: API Key exists -> {'Yes' if api_key else 'No'}")
    print(f"DEBUG: Base ID exists -> {'Yes' if base_id else 'No'}")
    if not api_key or not base_id:
        print("❌ CRITICAL ERROR: API Keys are missing in settings.py!")
        return False
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }    
    try:
        print(f"📡 Sending request to Airtable...")
        response = requests.post(url, json={"fields": fields}, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            print(f"✅ SUCCESS: Data is now inside Airtable table: {table_name}")
            return True
        else:
            print(f"❌ API ERROR ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")
        return False

def send_ai_reply_via_sendgrid(to_email, subject, content):
    
    from_email = From(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME)
    to_email_obj = To(to_email)
    content_obj = Content("text/plain", content)
    message = Mail(from_email, to_email_obj, subject, content_obj)
    
    try:
       
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"📧 SENDGRID STATUS: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ SENDGRID CRITICAL ERROR: {e}")
        return False

    from_email = From(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME)
    
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        

        print(f"📧 SENDGRID STATUS: {response.status_code}")
        
        if response.status_code == 202:
            print(f"✅ Email successfully accepted by SendGrid for {to_email}")
            return True
        else:
            print(f"⚠️ Email was not sent. Response: {response.body}")
            return False
            
    except Exception as e:
        print(f"❌ SENDGRID CRITICAL ERROR: {e}")
        return False


def handle_venue_outreach(booking_obj):

    from .models import Venue
    venue = Venue.objects.filter(city=booking_obj.city).order_by('priority').first()
    
    if venue:
       
        subject = f"ACTION REQUIRED: New Booking Request for {booking_obj.city}"
        content = f"Hi {venue.venue_name},\n\nWe have a booking on {booking_obj.date} at {booking_obj.time}. Are you available?\n\nPlease reply YES or NO."
        
        
        send_ai_reply_via_sendgrid(venue.contact_email, subject, content)


        request_fields = {
            "Linked Booking": [booking_obj.booking_id], 
            "Venue": venue.venue_name,
            "Email Sent": True,
            "Status": "Pending"
        }
        sync_to_airtable_pro("Venue Requests", request_fields)


def auto_sync_all_rezgo_locations():
    from .models import RezgoLocation
    params = {'transcode': settings.REZGO_CID, 'key': settings.REZGO_API_KEY, 'i': 'search'}
    try:
        response = requests.get("https://api.rezgo.com/json", params=params)
        data = response.json()
        if int(data.get('total', 0)) > 0:
            items = data.get('item', [])
            if isinstance(items, dict): items = [items]
            for item in items:
                RezgoLocation.objects.update_or_create(rezgo_uid=item.get('uid'), defaults={'city_name': item.get('item')})
            return True
    except:
        return False
