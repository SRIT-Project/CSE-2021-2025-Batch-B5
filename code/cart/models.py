from django.db import models

from shop.models import Product
from shop.models import Variation
from accounts.models import Account

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cart_id


class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    rental_type = models.CharField(max_length=10, choices=[("hourly", "Hourly"), ("daily", "Daily")],default='hourly')
    duration = models.IntegerField()
    is_active = models.BooleanField(default=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def sub_total(self):
        if self.rental_type == "hourly":
            return self.product.price * self.duration * self.quantity
        elif self.rental_type == "daily":
            return 24 * self.product.price * self.duration * self.quantity
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.name} ({self.rental_type} - {self.duration})"
    