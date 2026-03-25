import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import AIEmailLog
from .utils import generate_ai_reply  # নিশ্চিত করুন utils.py তে এই ফাংশনটি আছে
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    operation_summary="AI-Powered Email Support Webhook",
    operation_description="Receives customer email replies, processes them using OpenAI GPT-4 and Knowledge Base, and sends an automated reply.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['from', 'text'],
        properties={
            'from': openapi.Schema(type=openapi.TYPE_STRING, example="customer@example.com"),
            'subject': openapi.Schema(type=openapi.TYPE_STRING, example="Re: Booking Inquiry"),
            'text': openapi.Schema(type=openapi.TYPE_STRING, example="Can I change my booking time?"),
        }
    )
)
@api_view(['POST'])
def email_reply_webhook(request):
    """
    ইউজার ইমেইল রিপ্লাই দিলে এই ভিউটি OpenAI ব্যবহার করে বুদ্ধিমান উত্তর পাঠাবে।
    """
    try:
        # ১. ইনকামিং ডাটা রিসিভ করা (DRF এর মাধ্যমে সরাসরি request.data পাওয়া যায়)
        data = request.data
        sender_email = data.get('from')
        subject = data.get('subject', 'Inquiry Update')
        user_message = data.get('text', '')

        if not user_message:
            return Response({"error": "Message text is required"}, status=400)

        # ২. এআই ইঞ্জিন কল করা (এটি ডাটাবেজের FAQ পড়বে এবং OpenAI দিয়ে উত্তর লিখবে)
        ai_generated_answer = generate_ai_reply(user_message)

        # ৩. কাস্টমারকে চমৎকার এআই রিপ্লাই মেইল পাঠানো
        send_mail(
            subject=f"Re: {subject}",
            message=ai_generated_answer,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[sender_email],
            fail_silently=False,
        )

        # ৪. রেকর্ডের জন্য ডাটাবেজে সেভ করা (AIEmailLog)
        AIEmailLog.objects.create(
            user_email=sender_email,
            user_question=user_message,
            ai_response=ai_generated_answer
        )

        return Response({
            "status": "success",
            "message": "AI reply sent successfully",
            "ai_response": ai_generated_answer
        }, status=200)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)