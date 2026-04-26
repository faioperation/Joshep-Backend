from django.urls import path
from .views import email_reply_webhook,handle_email_reply_orchestrator

urlpatterns = [
    path('email-reply/', email_reply_webhook, name='email_reply'),
    # ata sandgrid emaila weebhook kora deva 
    path('email-reply-weebhook/', handle_email_reply_orchestrator,name='email_reply_orchestrator')
]