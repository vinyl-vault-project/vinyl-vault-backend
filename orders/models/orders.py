import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product


def generate_order_number():
    return f"VV-{uuid.uuid4().hex.upper()}"


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CANCELED = "CANCELED", "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    order_number = models.CharField(
        max_length=50,
        unique=True,
        default=generate_order_number,
        editable=False,
    )
    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    shipping_address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="order_total_gte_0",
            ),
        ]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.RESTRICT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_item_quantity_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="order_item_unit_price_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.order.order_number}: {self.product} x {self.quantity}"
