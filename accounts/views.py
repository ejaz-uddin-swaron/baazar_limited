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
import environ

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
    
class UserLoginApiView(APIView):
    def post(self, request):
        serializer = serializers.UserLoginSerializer(data=self.request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username,password=password)

        if user:
            token, _ = Token.objects.get_or_create(user=user)
            login(request, user)
            client = getattr(user, 'client', None)
            phone = client.mobile_no if client else None
            role = client.role if client else None 

            return Response({'token':token.key, 'user_id':user.id, 'username':user.username, 'phone':phone, 'role':role})
        else:
            return Response({'error':'invalid credentials'}, status=400)
        
        return Response(serializer.errors, status=400)
    
class UserLogoutView(APIView):
    def get(self, request):
        request.user.auth_token.delete()
        logout(request)
        return redirect('login')