import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from .models import AIEmailLog
from .utils import generate_ai_reply, send_ai_reply_via_sendgrid # নতুন ফাংশন ইম্পোর্ট করা হয়েছে
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    operation_summary="AI-Powered Email Support via SendGrid",
    operation_description="Receives customer email replies, processes them using OpenAI, and sends an automated reply through SendGrid API.",
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
    ইউজার ইমেইল রিপ্লাই দিলে এই ভিউটি OpenAI এবং SendGrid ব্যবহার করে উত্তর পাঠাবে।
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

        # ৩. সেন্ডগ্রিড এপিআই ব্যবহার করে কাস্টমারকে উত্তর পাঠানো
        # আমরা এখন settings.py এর SMTP ব্যবহার না করে সরাসরি API কল করছি
        email_sent = send_ai_reply_via_sendgrid(
            to_email=sender_email,
            subject=f"Re: {subject}",
            content=ai_generated_answer
        )

        # ৪. রেকর্ডের জন্য ডাটাবেজে সেভ করা (লগ রাখা)
        AIEmailLog.objects.create(
            user_email=sender_email,
            user_question=user_message,
            ai_response=ai_generated_answer
        )

        if email_sent:
            return Response({
                "status": "success",
                "message": "AI reply generated and sent via SendGrid.",
                "ai_answer": ai_generated_answer
            }, status=200)
        else:
            return Response({
                "status": "partial_success",
                "message": "AI generated answer, but SendGrid failed to send email. Check logs.",
                "ai_answer": ai_generated_answer
            }, status=500)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)