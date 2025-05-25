from rest_framework import generics, permissions
from .models import Order
from .serializers import OrderSerializer

class CreateOrderView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

