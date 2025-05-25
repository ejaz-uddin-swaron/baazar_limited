from rest_framework import generics, permissions
from .models import BillingAddress
from .serializers import BillingAddressSerializer

class BillingAddressCreateView(generics.CreateAPIView):
    queryset = BillingAddress.objects.all()
    serializer_class = BillingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
