import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from .models import AIEmailLog,AIHelpDesk
from .utils import generate_ai_reply, send_ai_reply_via_sendgrid,get_answer_from_ai_team_api  
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
    try:

        data = request.data
        sender_email = data.get('from')
        subject = data.get('subject', 'Inquiry Update')
        user_message = data.get('text', '')

        if not user_message:
            return Response({"error": "Message text is required"}, status=400)


        ai_generated_answer = generate_ai_reply(user_message)


        email_sent = send_ai_reply_via_sendgrid(
            to_email=sender_email,
            subject=f"Re: {subject}",
            content=ai_generated_answer
        )
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



@api_view(['POST'])

def handle_email_reply_orchestrator(request):

    try:

        user_email=request.data.get('from')
        user_question=request.data.get('text')
        email_subject=request.data.get('subject','Re: Your Inquiry')


        db_record = AIHelpDesk.objects.create(
            user_email=user_email,
            question=user_question
        )


        ai_team_answer=get_answer_from_ai_team_api(user_question)

        db_record.answer=ai_team_answer
        db_record.is_processed=True
        db_record.save()


        send_mail(
            subject=f"RE:{email_subject}",
            message=ai_team_answer,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            fail_silently=False
        )

        return Response({
            "status":"success",
            "message":"Full Automation Flow Completed",
            "ai_response":ai_team_answer
        },status=200)
    except Exception as e:
        return Response({"error":str(e)},status=400)

