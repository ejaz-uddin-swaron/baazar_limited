from django.db import models
import uuid

class Order(models.Model):
    order_code = models.CharField(max_length=100, unique=True, blank=True)
    food_category_id = models.IntegerField() 
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = "ORD" + uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)
