from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        VERIFY_TOKEN = "sujon_ai_secret_123"
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        return HttpResponse('Error', status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        
        # --- এই অংশটি মেটা থেকে আসা সব ডাটা প্রিন্ট করবে ---
        print("\n--- NEW DATA RECEIVED FROM META ---")
        print(json.dumps(data, indent=2)) 
        print("------------------------------------\n")

        try:
            value = data['entry'][0]['changes'][0]['value']
            
            # চেক করা হচ্ছে এটি কি কোনো মেসেজ নাকি শুধু স্ট্যাটাস আপডেট
            if 'messages' in value:
                message_obj = value['messages'][0]
                number = message_obj['from']
                text = message_obj.get('text', {}).get('body', 'No Text')
                
                print(f" MESSAGE DETECTED -> {{number: {number}, message: {text}}}")
            
            elif 'statuses' in value:
                status = value['statuses'][0]['status']
                print(f"ℹ STATUS UPDATE -> Message is {status}")

        except Exception as e:
            print(f" Error while parsing: {e}")
            
        return HttpResponse('EVENT_RECEIVED', status=200)