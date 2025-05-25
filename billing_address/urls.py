from django.urls import path
from .views import BillingAddressCreateView

urlpatterns = [
    path('create/', BillingAddressCreateView.as_view(), name='billing_address_create'),
]
