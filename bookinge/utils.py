import requests
import json
import time
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Content

def check_rezgo_availability(location_query, date_string, user_name="Unknown", preferred_time=None):
    params = {
        'transcode': settings.REZGO_CID,
        'key': settings.REZGO_API_KEY,
        'i': 'search',
        'q': location_query 
    }
    print(location_query)
    print("this is params", params)

    try:
        response = requests.get("https://api.rezgo.com/json", params=params)
        data = response.json()
        print("this is api response",data)
        print("\n" + "="*50)
        print(f" REQUEST FROM USER: {user_name}")
        print(f" SEARCHING FOR LOCATION: {location_query}")
        print(f" REQUESTED DATE: {date_string}")
        print("="*50)

        if int(data.get('total', 0)) > 0:
            items = data.get('item', [])
            if isinstance(items, dict): items = [items]
            
            for item in items:
                print(f" REZGO FOUND ITEM: {item.get('item')}")
                print(f" SLOT TIME: {item.get('time')}")
                print(f" ITEM UID: {item.get('uid')}")
                print(f" PRICE: {item.get('starting')} {item.get('currency_base')}")
                
                item_time = item.get('time', '').strip().lower()
                
                if preferred_time:
                    user_time = preferred_time.strip().lower().replace(" ", "").lstrip('0')
                    i_time_clean = item_time.replace(" ", "").lstrip('0')

                    if user_time == i_time_clean:
                        print(f" MATCH SUCCESS: {user_name} matched with {item_time}")
                        return {'time': item.get('time'), 'uid': item.get('uid')}
                else:
                    return {'time': item.get('time'), 'uid': item.get('uid')}
            
            print(" NO MATCH: Slot not available for requested time.")
        else:
            print(" REZGO API ERROR: No inventory found for this location.")
        
        return None
    except Exception as e:
        print(f" CRITICAL ERROR: {e}")
        return None
        
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

    if not settings.AIRTABLE_API_KEY or not settings.AIRTABLE_BASE_ID:
        return False

    url = f"https://api.airtable.com/v0/{settings.AIRTABLE_BASE_ID}/{table_name}"
    headers = {
        "Authorization": f"Bearer {settings.AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json={"fields": fields}, headers=headers)
        if response.status_code in [200, 201]:
            print(f"SUCCESS: Synced to Airtable -> {table_name}")
            return True
        return False
    except:
        return False
    if not settings.AIRTABLE_API_KEY or not settings.AIRTABLE_BASE_ID:
        print("❌ Airtable Keys Missing")
        return False

    url = f"https://api.airtable.com/v0/{settings.AIRTABLE_BASE_ID}/{table_name}"
    headers = {
        "Authorization": f"Bearer {settings.AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {"fields": fields}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            print(f"✅ Successfully synced to Airtable Table: {table_name}")
            return True
        else:
          
            print(f"❌ Airtable Error in {table_name}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Airtable Request Failed: {e}")
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

    params = {
        'transcode': settings.REZGO_CID,
        'key': settings.REZGO_API_KEY,
        'i': 'search', 
    }

    try:
        print("🚀 Fetching items from Rezgo... please wait.")
        response = requests.get("https://api.rezgo.com/json", params=params)
        data = response.json()

        total_items = int(data.get('total', 0))
        if total_items > 0:
            items = data.get('item', [])
            if isinstance(items, dict): items = [items]

            count = 0
            for item in items:
                name = item.get('item') 
                uid = item.get('uid')   
                
               
                RezgoLocation.objects.update_or_create(
                    rezgo_uid=uid,
                    defaults={'city_name': name}
                )
                count += 1
            
            print(f"✅ Success! {item.uid} {item.name} locations synced to your Django database.")
            return True
        else:
            print("❌ No items found in Rezgo.")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
