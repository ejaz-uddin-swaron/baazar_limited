from rest_framework import serializers
from .models import BillingAddress
from order.models import Order
from cryptography.fernet import Fernet
import os

class BillingAddressSerializer(serializers.ModelSerializer):
    encrypted_order_code = serializers.CharField(write_only=True)
    category_id = serializers.SerializerMethodField()

    class Meta:
        model = BillingAddress
        fields = ['id', 'first_name', 'last_name', 'country', 'street_address', 'city', 'state', 'zip_code', 'phone_number', 'email', 'extra_notes', 'created_at', 'user', 'order', 'encrypted_order_code', 'category_id']   
        read_only_fields = ['user', 'order']

    def validate_encrypted_order_code(self, value):
        key = os.environ.get('FERNET_SECRET_KEY')
        if not key:
            raise serializers.ValidationError("Encryption key not set on server.")
        try:
            f = Fernet(key.encode())
            decrypted = f.decrypt(value.encode()).decode()
        except Exception:
            raise serializers.ValidationError("Invalid or tampered order code.")

        try:
            order = Order.objects.get(order_code=decrypted)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order does not exist.")

        self.order_instance = order
        return value

    def create(self, validated_data):
        validated_data.pop('encrypted_order_code')
        return BillingAddress.objects.create(
            **validated_data,
            order=self.order_instance,
        )
    

    def get_category_id(self, obj):
        return obj.order.food_category_id if obj.order else None

