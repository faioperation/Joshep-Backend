import requests
import json
from django.conf import settings

def check_rezgo_availability(location_or_uid, date_string, preferred_time=None):
    params = {
        'transcode': settings.REZGO_CID,
        'key': settings.REZGO_API_KEY,
        'i': 'search',
        't': 'uid',        # We are now searching using UID
        'q': location_or_uid, # The UID will be sent here
        'd': date_string
    }

    try:
        response = requests.get("https://api.rezgo.com/json", params=params)
        data = response.json()
        
        print("--- REZGO RAW DATA ---")
        print(json.dumps(data, indent=2)) 

        if int(data.get('total', 0)) > 0:
            # When Rezgo searches by UID, the 'item' field may return directly as a dictionary
            items = data.get('item', [])
            if isinstance(items, dict): 
                items = [items]
            
            for item in items:
                # If there are multiple options (for example: 'Manchester Session')
                # Rezgo search results may require checking the 'option' field as well
                item_time = item.get('time', '').strip()
                availability = int(item.get('date', {}).get('availability', 0))
                
                if preferred_time:
                    if preferred_time.lower() in item_time.lower() and availability > 0:
                        return [{
                            'time': item_time,
                            'booking_url': f"https://{settings.REZGO_DOMAIN}.rezgo.com/book?item={item.get('uid')}&date={date_string}"
                        }]
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []