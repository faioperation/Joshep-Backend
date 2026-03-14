import requests
import json
from django.conf import settings
import time 

def check_rezgo_availability(item_uid, date_string, preferred_time=None):
    """
    Check availability from Rezgo Search API using Item UID and date.
    Optionally filters by preferred time if provided.
    """
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

        # Check if any results are returned
        if int(data.get('total', 0)) > 0:
            items = data.get('item', [])

            # Ensure the response is always treated as a list
            if isinstance(items, dict):
                items = [items]

            for item in items:
                item_time = item.get('time', '').strip()
                availability = int(item.get('date', {}).get('availability', 0))

                # If a preferred time is provided, match the time
                if preferred_time:
                    if preferred_time.lower() in item_time.lower() and availability > 0:
                        return {'time': item_time, 'uid': item_uid}

                # Otherwise return the first available slot
                elif availability > 0:
                    return {'time': item_time, 'uid': item_uid}

        return None

    except:
        return None


def commit_rezgo_booking(data, item_uid):
    """
    Final function used to confirm a booking in Rezgo.
    Sends an XML commit request to the Rezgo Booking API.
    """

    URL = "https://api.rezgo.com/xml"
    
    # Generate a unique reference ID for each booking request
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

    # Define request headers for XML payload
    headers = {'Content-Type': 'application/xml'}

    try:
        response = requests.post(URL, data=xml_payload, headers=headers)

        print("\n" + "="*40)
        print("REZGO COMMIT RESPONSE (XML):")
        print(response.text) 
        print("="*40 + "\n")

        return response.text

    except Exception as e:
        print(f"Commit Error: {e}")
        return None