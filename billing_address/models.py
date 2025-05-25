from django.db import models
from django.contrib.auth.models import User
from order.models import Order

class BillingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    street_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    extra_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)