from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from catalog.models import Product
from orders.exceptions import OrderCancellationConflict
from orders.models import Cart, CartItem, Order, OrderItem


def fill_missing_user_profile(user, order):
    updated_fields = []

    if not user.first_name:
        user.first_name = order.first_name
        updated_fields.append("first_name")

    if not user.last_name:
        user.last_name = order.last_name
        updated_fields.append("last_name")

    if not user.phone:
        user.phone = order.phone
        updated_fields.append("phone")

    if not user.address:
        user.address = order.shipping_address
        updated_fields.append("address")

    if updated_fields:
        user.save(update_fields=updated_fields)


def checkout(*, user, checkout_data):
    with transaction.atomic():
        cart = Cart.objects.select_for_update().filter(user=user).first()
        if cart is None:
            raise ValidationError({"detail": "Cart is empty."})

        cart_items = list(
            CartItem.objects.select_for_update().filter(cart=cart).order_by("pk")
        )
        if not cart_items:
            raise ValidationError({"detail": "Cart is empty."})

        product_ids = [item.product_id for item in cart_items]
        locked_products = (
            Product.objects.select_for_update()
            .filter(id__in=product_ids)
            .order_by("pk")
        )
        locked_products_by_id = {product.pk: product for product in locked_products}

        for item in cart_items:
            product = locked_products_by_id[item.product_id]

            if not product.is_active:
                raise ValidationError(
                    {
                        "detail": "Product is no longer available.",
                        "product_id": product.id,
                    }
                )

            if item.quantity > product.stock_quantity:
                raise ValidationError(
                    {
                        "detail": "Not enough stock for this product.",
                        "product_id": product.id,
                    }
                )

        total = sum(
            (
                locked_products_by_id[item.product_id].price * item.quantity
                for item in cart_items
            ),
            start=Decimal("0.00"),
        )

        order = Order.objects.create(user=user, total=total, **checkout_data)
        order_items = []
        products_to_update = []

        for item in cart_items:
            product = locked_products_by_id[item.product_id]
            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    unit_price=product.price,
                )
            )
            product.stock_quantity -= item.quantity
            products_to_update.append(product)

        Product.objects.bulk_update(products_to_update, ["stock_quantity"])
        OrderItem.objects.bulk_create(order_items)

        CartItem.objects.filter(cart=cart).delete()
        cart.save(update_fields=["updated_at"])
        fill_missing_user_profile(user=user, order=order)

    return order


def cancel_order(*, order):
    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=order.pk)

        if locked_order.status != Order.OrderStatus.PENDING:
            raise OrderCancellationConflict()

        order_items = list(
            OrderItem.objects.filter(order=locked_order).order_by("product_id")
        )

        product_ids = [item.product_id for item in order_items]
        products = list(
            Product.objects.select_for_update()
            .filter(id__in=product_ids)
            .order_by("id")
        )
        products_by_id = {product.pk: product for product in products}

        for item in order_items:
            product = products_by_id[item.product_id]
            product.stock_quantity += item.quantity

        Product.objects.bulk_update(list(products_by_id.values), ["stock_quantity"])

        locked_order.status = Order.OrderStatus.CANCELED
        locked_order.save(update_fields=["status", "updated_at"])

    return locked_order
