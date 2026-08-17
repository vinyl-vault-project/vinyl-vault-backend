from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from catalog.models import Product, Release
from orders.models import Cart, CartItem


User = get_user_model()


class CartModelTests(TestCase):
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
        self.cart = Cart.objects.create(user=self.user)

    def test_user_can_have_only_one_cart(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Cart.objects.create(user=self.user)

    def test_cart_cannot_contain_same_product_twice(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            CartItem.objects.create(
                cart=self.cart,
                product=self.product,
                quantity=1,
            )

    def test_cart_item_quantity_must_be_at_least_one(self):
        item = CartItem(
            cart=self.cart,
            product=self.product,
            quantity=0,
        )

        with self.assertRaises(ValidationError):
            item.full_clean()
