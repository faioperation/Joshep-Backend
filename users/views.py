from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
from rest_framework import viewsets
from .serializers import FAQSerializers,ResetPasswordSerializer
from django.contrib.auth import logout
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.core.cache import cache

# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt
from.models import FAQ
from .models import Users
from .serializers import (
    LoginSerializer,
    ForgotPasswordSerializer,
    OTPVerifySerializer,
    ResetPasswordSerializer,
)

OTP_STORAGE = {}   

 
class LoginView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            
 
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "email": user.email
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = str(random.randint(100000, 999999))

        OTP_STORAGE[email] = {
            "otp": otp,
            "expires": timezone.now() + timedelta(minutes=5)
        }

        send_mail(
            "Your OTP Code",
            f"Your OTP is {otp}",
            "noreply@example.com",
            [email],
        )

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        data = OTP_STORAGE.get(email)

        if not data:
            return Response({"error": "OTP not found"}, status=400)

        if data["expires"] < timezone.now():
            return Response({"error": "OTP expired"}, status=400)

        if data["otp"] != otp:
            return Response({"error": "Invalid OTP"}, status=400)

        return Response({"message": "OTP verified"}, status=200)
    def verify_otp(email, otp):
        stored_otp = cache.get(f"otp_{email}")

        if not stored_otp:
            return False

        if stored_otp != otp:
            return False

        cache.delete(f"otp_{email}")
        return True
    
class ResendOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")

        if not Users.objects.filter(email=email).exists():
            return Response({"error": "User not found"}, status=400)

        otp = str(random.randint(100000, 999999))

        OTP_STORAGE[email] = {
            "otp": otp,
            "expires": timezone.now() + timedelta(minutes=5)
        }

        send_mail(
            "Your New OTP Code",
            f"Your OTP is {otp}",
            "noreply@example.com",
            [email],
        )

        return Response({"message": "OTP resent successfully"}, status=200)
class FAQViewSet(viewsets.ModelViewSet):
    queryset=FAQ.objects.all()
    serializer_class=FAQSerializers
    
class ResetPasswordView(APIView):

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        new_password = serializer.validated_data.get("new_password")
        

        try:
            user = Users.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            

            if email in OTP_STORAGE:
                del OTP_STORAGE[email]
                
            return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)