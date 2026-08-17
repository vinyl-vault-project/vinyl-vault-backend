from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Artist, Product, Release
from orders.models import Cart, CartItem


User = get_user_model()


class CartApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="listener@example.com",
            username="listener",
            password="StrongPassword123!",
        )
        artist = Artist.objects.create(
            name="Test Artist",
            slug="test-artist",
        )
        release = Release.objects.create(
            title="Test Album",
            slug="test-album",
            release_year=2024,
        )
        release.artists.add(artist)
        self.product = Product.objects.create(
            release=release,
            pressing_country="UA",
            price=Decimal("25.00"),
            stock_quantity=3,
        )
        self.cart_url = reverse("orders:cart-detail")
        self.items_url = reverse("orders:cart-item-list")
        self.client.force_authenticate(self.user)

    def test_cart_endpoints_require_authentication(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )
        item_url = reverse(
            "orders:cart-item-detail",
            kwargs={"item_id": item.pk},
        )
        self.client.force_authenticate(user=None)

        requests = (
            ("get", self.cart_url, None),
            ("post", self.items_url, {"product_id": self.product.pk}),
            ("patch", item_url, {"quantity": 2}),
            ("delete", item_url, None),
        )

        for method, url, data in requests:
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    url,
                    data,
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

    def test_get_cart_returns_items_with_current_price_and_total(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )
        self.product.price = Decimal("30.00")
        self.product.save(update_fields=["price"])

        response = self.client.get(self.cart_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], "60.00")
        self.assertEqual(len(response.data["items"]), 1)
        item_data = response.data["items"][0]
        self.assertEqual(item_data["subtotal"], "60.00")
        self.assertEqual(item_data["product"]["price"], "30.00")
        self.assertEqual(
            item_data["product"]["release"]["title"],
            "Test Album",
        )

    def test_add_item_uses_default_quantity(self):
        response = self.client.post(
            self.items_url,
            {"product_id": self.product.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = CartItem.objects.get()
        self.assertEqual(item.cart.user, self.user)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(response.data["quantity"], 1)

    def test_add_item_rejects_invalid_availability_or_quantity(self):
        cases = (
            {"is_active": False, "stock": 3, "quantity": 1, "field": "product_id"},
            {"is_active": True, "stock": 0, "quantity": 1, "field": "quantity"},
            {"is_active": True, "stock": 2, "quantity": 3, "field": "quantity"},
            {"is_active": True, "stock": 3, "quantity": 0, "field": "quantity"},
        )

        for case in cases:
            with self.subTest(case=case):
                self.product.is_active = case["is_active"]
                self.product.stock_quantity = case["stock"]
                self.product.save(update_fields=["is_active", "stock_quantity"])

                response = self.client.post(
                    self.items_url,
                    {
                        "product_id": self.product.pk,
                        "quantity": case["quantity"],
                    },
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertIn(case["field"], response.data)
                self.assertFalse(CartItem.objects.exists())

    def test_add_same_product_twice_returns_conflict(self):
        payload = {"product_id": self.product.pk, "quantity": 1}
        first_response = self.client.post(
            self.items_url,
            payload,
            format="json",
        )

        second_response = self.client.post(
            self.items_url,
            payload,
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_update_quantity_validates_stock(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )
        item_url = reverse(
            "orders:cart-item-detail",
            kwargs={"item_id": item.pk},
        )

        response = self.client.patch(
            item_url,
            {"quantity": 3},
            format="json",
        )
        overstock_response = self.client.patch(
            item_url,
            {"quantity": 4},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 3)
        self.assertEqual(
            overstock_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

    def test_user_cannot_update_or_delete_another_users_item(self):
        other_user = User.objects.create_user(
            email="other@example.com",
            username="other-user",
            password="StrongPassword123!",
        )
        item = CartItem.objects.create(
            cart=Cart.objects.create(user=other_user),
            product=self.product,
            quantity=1,
        )
        item_url = reverse(
            "orders:cart-item-detail",
            kwargs={"item_id": item.pk},
        )

        patch_response = self.client.patch(
            item_url,
            {"quantity": 2},
            format="json",
        )
        delete_response = self.client.delete(item_url)

        self.assertEqual(patch_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_delete_removes_own_cart_item(self):
        item = CartItem.objects.create(
            cart=Cart.objects.create(user=self.user),
            product=self.product,
            quantity=1,
        )
        item_url = reverse(
            "orders:cart-item-detail",
            kwargs={"item_id": item.pk},
        )

        response = self.client.delete(item_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())
