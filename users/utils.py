# utils.py
import random
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
def generate_and_save_otp(email):
    otp = str(random.randint(100000, 999999))
    cache.set(f"otp_{email}", otp, timeout=300)
    return otp

def send_otp_email(email, otp):
    subject = "Your Spartacus AI Verification Code"
    message = f"Your OTP for signup/password reset is: {otp}. It will expire in 5 minutes."
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, [email])