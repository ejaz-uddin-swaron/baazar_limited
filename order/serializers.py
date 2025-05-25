from rest_framework import serializers
from .models import Order
import requests
from cryptography.fernet import Fernet
from django.conf import settings

class OrderSerializer(serializers.ModelSerializer):
    encrypted_order_code = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'encrypted_order_code', 'food_category_id', 'created_at']
        read_only_fields = ['order_code', 'created_at']

    def get_encrypted_order_code(self, obj):
        key = settings.FERNET_SECRET_KEY.encode()
        f = Fernet(key)
        encrypted = f.encrypt(obj.order_code.encode())
        return encrypted.decode()

    def validate_category_id(self, value):
        url = f"https://baazar-ltd.onrender.com/api-docs/#/Categories/get_api_category__id_/"
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise serializers.ValidationError("Invalid food category.")
        except requests.exceptions.RequestException:
            raise serializers.ValidationError("Failed to connect to category service.")
        
        return value
