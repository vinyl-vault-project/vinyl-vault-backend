from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Artist, Label, Product, Release
from orders.models import Cart, CartItem, Order, OrderItem

User = get_user_model()


class OrderApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="listener@example.com",
            username="listener",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            username="other-listener",
            password="StrongPassword123!",
        )
        self.artist = Artist.objects.create(
            name="Test Artist",
            slug="test-artist",
        )
        self.label = Label.objects.create(
            name="Test Label",
            slug="test-label",
        )
        self.product = self.create_product(
            title="Test Album",
            slug="test-album",
            price=Decimal("25.00"),
            stock_quantity=3,
        )
        self.product.labels.add(self.label)
        self.orders_url = reverse("orders:order-list")
        self.client.force_authenticate(self.user)

    def create_product(
        self,
        *,
        title,
        slug,
        price,
        stock_quantity=5,
        is_active=True,
    ):
        release = Release.objects.create(
            title=title,
            slug=slug,
            release_year=2024,
            cover_url=f"https://example.com/{slug}.jpg",
        )
        release.artists.add(self.artist)
        return Product.objects.create(
            release=release,
            pressing_country="UA",
            price=price,
            stock_quantity=stock_quantity,
            is_active=is_active,
        )

    def create_order(self, *, user=None, **overrides):
        data = {
            "user": user or self.user,
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

    def checkout_payload(self, **overrides):
        data = {
            "first_name": "Sem",
            "last_name": "Bib",
            "email": "sem@example.com",
            "phone": "+49123456789",
            "city": "Pforzheim",
            "shipping_address": "Hauptstr. 12",
            "postal_code": "75172",
            "country": "Germany",
        }
        data.update(overrides)
        return data

    def test_order_endpoints_require_authentication(self):
        order = self.create_order()
        detail_url = reverse(
            "orders:order-detail",
            kwargs={"order_number": order.order_number},
        )
        cancel_url = reverse(
            "orders:order-cancel",
            kwargs={"order_number": order.order_number},
        )
        self.client.force_authenticate(user=None)

        requests = (
            ("get", self.orders_url, None),
            ("post", self.orders_url, self.checkout_payload()),
            ("get", detail_url, None),
            ("post", cancel_url, None),
        )

        for method, url, data in requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(
                    url,
                    data,
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

    def test_checkout_creates_order_updates_stock_and_clears_cart(self):
        second_product = self.create_product(
            title="Second Album",
            slug="second-album",
            price=Decimal("15.00"),
            stock_quantity=5,
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )
        CartItem.objects.create(
            cart=cart,
            product=second_product,
            quantity=3,
        )

        response = self.client.post(
            self.orders_url,
            self.checkout_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, Order.OrderStatus.PENDING)
        self.assertEqual(order.total, Decimal("95.00"))
        self.assertEqual(order.first_name, "Sem")
        self.assertEqual(order.shipping_address, "Hauptstr. 12")

        order_items = list(order.items.order_by("product_id"))
        self.assertEqual(len(order_items), 2)
        snapshots = {
            item.product_id: (item.quantity, item.unit_price) for item in order_items
        }
        self.assertEqual(snapshots[self.product.pk], (2, Decimal("25.00")))
        self.assertEqual(snapshots[second_product.pk], (3, Decimal("15.00")))

        self.product.refresh_from_db()
        second_product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 1)
        self.assertEqual(second_product.stock_quantity, 2)
        self.assertTrue(Cart.objects.filter(pk=cart.pk).exists())
        self.assertFalse(CartItem.objects.filter(cart=cart).exists())

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Sem")
        self.assertEqual(self.user.last_name, "Bib")
        self.assertEqual(self.user.phone, "+49123456789")
        self.assertEqual(self.user.address, "Hauptstr. 12")

        self.assertEqual(response.data["order_number"], order.order_number)
        self.assertEqual(response.data["line_items_count"], 2)
        self.assertEqual(response.data["subtotal"], "95.00")
        self.assertEqual(response.data["total"], "95.00")
        self.assertEqual(
            response.data["checkout_data"],
            self.checkout_payload(),
        )

    def test_checkout_does_not_overwrite_existing_user_profile_data(self):
        self.user.first_name = "Existing"
        self.user.phone = "+380000000000"
        self.user.address = "Existing address"
        self.user.save(update_fields=["first_name", "phone", "address"])
        CartItem.objects.create(
            cart=Cart.objects.create(user=self.user),
            product=self.product,
            quantity=1,
        )

        response = self.client.post(
            self.orders_url,
            self.checkout_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Existing")
        self.assertEqual(self.user.last_name, "Bib")
        self.assertEqual(self.user.phone, "+380000000000")
        self.assertEqual(self.user.address, "Existing address")

    def test_checkout_rejects_empty_cart(self):
        for create_cart in (False, True):
            with self.subTest(cart_exists=create_cart):
                Cart.objects.filter(user=self.user).delete()
                if create_cart:
                    Cart.objects.create(user=self.user)

                response = self.client.post(
                    self.orders_url,
                    self.checkout_payload(),
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertEqual(response.data["detail"], "Cart is empty.")
                self.assertFalse(Order.objects.exists())

    def test_checkout_revalidates_products_without_partial_changes(self):
        valid_product = self.create_product(
            title="Valid Album",
            slug="valid-album",
            price=Decimal("10.00"),
            stock_quantity=4,
        )

        cases = (
            {
                "is_active": False,
                "stock_quantity": 3,
                "detail": "Product is no longer available.",
            },
            {
                "is_active": True,
                "stock_quantity": 1,
                "detail": "Not enough stock for this product.",
            },
        )

        for case in cases:
            with self.subTest(case=case):
                Cart.objects.filter(user=self.user).delete()
                cart = Cart.objects.create(user=self.user)
                CartItem.objects.create(
                    cart=cart,
                    product=valid_product,
                    quantity=1,
                )
                CartItem.objects.create(
                    cart=cart,
                    product=self.product,
                    quantity=2,
                )
                self.product.is_active = case["is_active"]
                self.product.stock_quantity = case["stock_quantity"]
                self.product.save(update_fields=["is_active", "stock_quantity"])

                response = self.client.post(
                    self.orders_url,
                    self.checkout_payload(),
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertEqual(response.data["detail"], case["detail"])
                self.assertEqual(response.data["product_id"], str(self.product.pk))
                self.assertFalse(Order.objects.exists())
                self.assertEqual(CartItem.objects.filter(cart=cart).count(), 2)

                valid_product.refresh_from_db()
                self.product.refresh_from_db()
                self.assertEqual(valid_product.stock_quantity, 4)
                self.assertEqual(
                    self.product.stock_quantity,
                    case["stock_quantity"],
                )

    def test_invalid_checkout_data_does_not_change_cart(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
        )

        response = self.client.post(
            self.orders_url,
            self.checkout_payload(email="not-an-email"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertFalse(Order.objects.exists())
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

    def test_list_returns_only_current_users_orders_in_expected_shape(self):
        older_order = self.create_order(total=Decimal("50.00"))
        OrderItem.objects.create(
            order=older_order,
            product=self.product,
            quantity=2,
            unit_price=Decimal("25.00"),
        )
        newer_order = self.create_order(
            status=Order.OrderStatus.CANCELED,
            total=Decimal("75.00"),
        )
        OrderItem.objects.create(
            order=newer_order,
            product=self.product,
            quantity=3,
            unit_price=Decimal("25.00"),
        )
        other_order = self.create_order(user=self.other_user)
        OrderItem.objects.create(
            order=other_order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("25.00"),
        )

        response = self.client.get(self.orders_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            [item["order_number"] for item in response.data],
            [newer_order.order_number, older_order.order_number],
        )
        newest_data = response.data[0]
        self.assertEqual(newest_data["status"], Order.OrderStatus.CANCELED)
        self.assertEqual(newest_data["total_quantity"], 3)
        self.assertEqual(newest_data["total"], "75.00")
        self.assertEqual(newest_data["items"][0]["quantity"], 3)
        self.assertEqual(
            newest_data["items"][0]["product"]["release"]["title"],
            "Test Album",
        )
        self.assertEqual(
            newest_data["items"][0]["product"]["release"]["cover_url"],
            "https://example.com/test-album.jpg",
        )

    def test_list_query_count_does_not_grow_with_number_of_orders(self):
        for quantity in range(1, 6):
            order = self.create_order(total=Decimal("25.00") * quantity)
            OrderItem.objects.create(
                order=order,
                product=self.product,
                quantity=quantity,
                unit_price=Decimal("25.00"),
            )

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.orders_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(queries), 2)

    def test_retrieve_returns_order_details_using_price_snapshot(self):
        order = self.create_order(total=Decimal("50.00"))
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal("25.00"),
        )
        self.product.price = Decimal("99.00")
        self.product.save(update_fields=["price"])
        detail_url = reverse(
            "orders:order-detail",
            kwargs={"order_number": order.order_number},
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["line_items_count"], 1)
        self.assertEqual(response.data["subtotal"], "50.00")
        self.assertEqual(response.data["total"], "50.00")
        item_data = response.data["items"][0]
        self.assertEqual(item_data["unit_price"], "25.00")
        self.assertEqual(item_data["subtotal"], "50.00")
        self.assertEqual(
            item_data["product"]["release"]["artists"][0]["name"],
            "Test Artist",
        )
        self.assertEqual(
            item_data["product"]["labels"][0]["name"],
            "Test Label",
        )
        self.assertEqual(
            response.data["checkout_data"]["shipping_address"],
            "1 Music Street",
        )

    def test_user_cannot_retrieve_another_users_order(self):
        order = self.create_order(user=self.other_user)
        detail_url = reverse(
            "orders:order-detail",
            kwargs={"order_number": order.order_number},
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_pending_order_restores_stock(self):
        order = self.create_order(total=Decimal("50.00"))
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal("25.00"),
        )
        self.product.stock_quantity = 1
        self.product.save(update_fields=["stock_quantity"])
        cancel_url = reverse(
            "orders:order-cancel",
            kwargs={"order_number": order.order_number},
        )

        response = self.client.post(cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.CANCELED)
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertEqual(response.data["status"], Order.OrderStatus.CANCELED)
        self.assertEqual(response.data["items"][0]["quantity"], 2)

    def test_canceling_non_pending_order_returns_conflict_once(self):
        order = self.create_order(total=Decimal("25.00"))
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("25.00"),
        )
        cancel_url = reverse(
            "orders:order-cancel",
            kwargs={"order_number": order.order_number},
        )

        first_response = self.client.post(cancel_url)
        second_response = self.client.post(cancel_url)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            second_response.data["detail"],
            "Only pending orders can be canceled.",
        )
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.CANCELED)
        self.assertEqual(self.product.stock_quantity, 4)

    def test_user_cannot_cancel_another_users_order(self):
        order = self.create_order(user=self.other_user)
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("25.00"),
        )
        cancel_url = reverse(
            "orders:order-cancel",
            kwargs={"order_number": order.order_number},
        )

        response = self.client.post(cancel_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.PENDING)
        self.assertEqual(self.product.stock_quantity, 3)
