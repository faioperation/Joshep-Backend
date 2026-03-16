import requests
import json
import time
from django.conf import settings

# ১. রেজগো স্লট চেক করার ফাংশন
def check_rezgo_availability(item_uid, date_string, preferred_time=None):
    params = {
        'transcode': settings.REZGO_CID,
        'key': settings.REZGO_API_KEY,
        'i': 'search',
        't': 'uid',
        'q': item_uid,
        'd': date_string
    }
    try:
        response = requests.get("https://api.rezgo.com/json", params=params)
        data = response.json()
        if int(data.get('total', 0)) > 0:
            items = data.get('item', [])
            if isinstance(items, dict): items = [items]
            for item in items:
                item_time = item.get('time', '').strip()
                availability = int(item.get('date', {}).get('availability', 0))
                if preferred_time:
                    if preferred_time.lower() in item_time.lower() and availability > 0:
                        return {'time': item_time, 'uid': item_uid}
                elif availability > 0:
                    return {'time': item_time, 'uid': item_uid}
        return None
    except:
        return None

# ২. রেজগো বুকিং কনফার্ম (Commit) করার ফাংশন
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
            <tour_phone_number>{data.get('phone', '000000')}</tour_phone_number>
            <payment_method>Cash</payment_method>
            <agree_terms>1</agree_terms>
            <status>1</status>
            <refid>{ref_id}</refid>
            <ip>127.0.0.1</ip>
        </payment>
    </request>"""
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(URL, data=xml_payload, headers=headers)
        return response.text
    except:
        return None

# ৩. এয়ারটেবল সিঙ্ক করার ফাংশন
def sync_to_airtable(inquiry_obj):
    if not settings.AIRTABLE_API_KEY or not settings.AIRTABLE_BASE_ID:
        print("❌ Airtable Error: API Key or Base ID missing in .env")
        return

    url = f"https://api.airtable.com/v0/{settings.AIRTABLE_BASE_ID}/Inquiries"
    headers = {
        "Authorization": f"Bearer {settings.AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "fields": {
            "Name": inquiry_obj.name,
            "Phone": inquiry_obj.phone,
            "Email": inquiry_obj.email,
            "Location": inquiry_obj.location,
            "Date": str(inquiry_obj.preferred_date),
            "Time": inquiry_obj.preferred_time or "Not Set",
            "Status": "Confirmed" if inquiry_obj.is_available else "Pending"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ Successfully synced to Airtable: {inquiry_obj.name}")
        else:
            print(f"❌ Airtable API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Airtable Request Failed: {e}")