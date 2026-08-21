from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from catalog.models import Product, Release
from orders.models import Order, OrderItem

User = get_user_model()


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="listener@example.com",
            username="listener",
            password="StrongPassword123!",
        )
        release = Release.objects.create(
            title="Test Album",
            slug="test-album",
        )
        self.product = Product.objects.create(
            release=release,
            pressing_country="UA",
            price=Decimal("25.00"),
            stock_quantity=3,
        )

    def create_order(self, **overrides):
        data = {
            "user": self.user,
            "first_name": "Test",
            "last_name": "Listener",
            "email": "checkout@example.com",
            "phone": "+380501234567",
            "city": "Kyiv",
            "shipping_address": "1 Music Street",
            "postal_code": "01001",
            "country": "Ukraine",
            "total": Decimal("25.00"),
        }
        data.update(overrides)
        return Order.objects.create(**data)

    def test_order_number_is_generated_and_globally_unique(self):
        first_order = self.create_order()
        second_order = self.create_order()

        self.assertTrue(first_order.order_number.startswith("VV-"))
        self.assertNotEqual(first_order.order_number, second_order.order_number)

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_order(order_number=first_order.order_number)

    def test_order_defaults_to_pending_status(self):
        order = self.create_order()

        self.assertEqual(order.status, Order.OrderStatus.PENDING)

    def test_order_validates_email_format(self):
        order = self.create_order(email="invalid-email")

        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_order_total_cannot_be_negative(self):
        order = Order(
            user=self.user,
            first_name="Test",
            last_name="Listener",
            email="checkout@example.com",
            phone="+380501234567",
            city="Kyiv",
            shipping_address="1 Music Street",
            postal_code="01001",
            country="Ukraine",
            total=Decimal("-0.01"),
        )

        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_order_item_stores_purchase_price_snapshot(self):
        order = self.create_order()
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
        )
        self.product.price = Decimal("30.00")
        self.product.save(update_fields=["price"])

        item.refresh_from_db()

        self.assertEqual(item.unit_price, Decimal("25.00"))

    def test_order_item_quantity_must_be_at_least_one(self):
        item = OrderItem(
            order=self.create_order(),
            product=self.product,
            quantity=0,
            unit_price=Decimal("25.00"),
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_order_item_unit_price_cannot_be_negative(self):
        item = OrderItem(
            order=self.create_order(),
            product=self.product,
            quantity=1,
            unit_price=Decimal("-0.01"),
        )

        with self.assertRaises(ValidationError):
            item.full_clean()
