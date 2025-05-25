from django.shortcuts import render
from rest_framework import viewsets
from . import models
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from supabase import create_client
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
import environ
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from drf_yasg import openapi

env = environ.Env()
environ.Env.read_env()

SUPABASE_URL = env("SUPABASE_URL")
SUPABASE_KEY = env("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create your views here.

class ClientViewset(viewsets.ModelViewSet):
    queryset = models.Client.objects.all()
    serializer_class = serializers.ClientSerializer

class UserRegistrationApiView(APIView):
    serializer_class = serializers.RegistratonSerializer

    @swagger_auto_schema(request_body=serializers.RegistratonSerializer)
    def post(self, request):
        serializer = self.serializer_class(data = request.data)

        if serializer.is_valid():
            user = serializer.save()
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            confirm_link = f'http://127.0.0.1:8000/client/active/{uid}/{token}/'
            email_subject = 'Confirmation email'
            email_body = render_to_string('confirm_email.html', {'confirm_link':confirm_link})
            email = EmailMultiAlternatives(email_subject, '', to=[user.email])
            email.attach_alternative(email_body, 'text/html')
            email.send()

            client = getattr(user, 'client', None)
            phone_number = client.mobile_no if client else None

            data = {
                "id": user.id,
                "username": user.username,
                "phone":phone_number,
                "role":"customer"
            }

            response = supabase.table("users").insert(data).execute()

            if hasattr(response, 'error') and response.error:
                return Response({"error": "Failed to save user in Supabase"}, status=400)

            return Response({'message': 'Check your email for confirmation'}, status=201)

        return Response(serializer.errors, status=400)
    
def activate(request, uid64, token):
    try:
        uid = urlsafe_base64_decode(uid64).decode()
        user = User._default_manager.get(pk=uid)
    except(User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        
        return redirect('login')
    else:
        return redirect('register')
    
class CustomUserLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_description="JWT login and return token with extra user info",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
            }
        ),
        responses={200: openapi.Response(
            description='Login successful',
            examples={
                "application/json": {
                    "refresh": "<refresh_token>",
                    "access": "<access_token>",
                    "user_id": 1,
                    "username": "exampleuser",
                    "phone": "01234567890",
                    "role": "client"
                }
            }
        )}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
class UserLogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logout a user by blacklisting the refresh token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['refresh']
        ),
        security=[{'Bearer': []}]
    )

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist() 

            return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid token or already blacklisted"}, status=status.HTTP_400_BAD_REQUEST)