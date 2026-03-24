import requests
import json
import time
from django.conf import settings

def check_rezgo_availability(location_query, date_string, preferred_time=None):
    # আমরা এখন আরও স্মার্টভাবে খুঁজবো
    # প্রথমে তারিখ ছাড়াই আইটেমটি খুঁজবো যাতে রেজগোর ক্যালেন্ডার বাগ আমাদের আটকাতে না পারে
    params = {
        'transcode': settings.REZGO_CID,
        'key': settings.REZGO_API_KEY,
        'i': 'search',
        'q': location_query # এখানে আপনার সেই ৪১৯৬৯০ আইডি বা নাম থাকবে
    }

    try:
        response = requests.get("https://api.rezgo.com/json", params=params)
        data = response.json()
        
        print(f"\n--- AI MASTER CHECK FOR: {location_query} ---")

        if int(data.get('total', 0)) > 0:
            items = data.get('item', [])
            if isinstance(items, dict): items = [items]
            
            for item in items:
                item_time = item.get('time', '').strip().lower()
                # যেহেতু আইটেমটি 'Always Available', আমরা ধরে নেবো স্লট খালি আছে
                is_always_avail = item.get('date_selection') == 'always'
                
                # যদি রেজগো তারিখ অনুযায়ী ডাটা না-ও দেয়, আমরা ম্যানুয়ালি টাইম চেক করবো
                print(f"Checking Item: {item.get('item')} | Time: {item_time}")

                if preferred_time:
                    user_time = preferred_time.strip().lower()
                    # সময় ম্যাচিং লজিক (2:00 PM vs 02:00 PM হ্যান্ডেল করবে)
                    if (user_time in item_time or item_time in user_time):
                        return {'time': item.get('time'), 'uid': item.get('uid')}
                else:
                    return {'time': item.get('time'), 'uid': item.get('uid')}
        
        print("Final Result: No matching item found in Rezgo.")
        return None
    except Exception as e:
        print(f"Critical Error: {e}")
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

# ৩. এয়ারটেবল জেনেরিক সিঙ্ক ফাংশন (FIXED)
def sync_to_airtable_generic(table_name, fields):
    if not settings.AIRTABLE_API_KEY or not settings.AIRTABLE_BASE_ID:
        print("❌ Airtable Keys Missing")
        return False

    # এখানে URL একদম নিখুঁত করা হয়েছে
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
            # এরর মেসেজ দেখার জন্য প্রিন্ট
            print(f"❌ Airtable Error in {table_name}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Airtable Request Failed: {e}")
        return False