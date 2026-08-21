from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from catalog.models import Product
from orders.exceptions import ProductAlreadyInCartConflict
from orders.models import Cart, CartItem


def _validate_product(product, quantity):
    if not product.is_active:
        raise ValidationError(
            {"product_id": "This product is not available."}
        )
    if quantity > product.stock_quantity:
        raise ValidationError(
            {
                "quantity": (
                    "Quantity cannot exceed the available stock "
                    f"of {product.stock_quantity}."
                )
            }
        )


def _get_locked_cart_item(*, user, item_id):
    cart_id = (
        CartItem.objects.filter(pk=item_id, cart__user=user)
        .values_list("cart_id", flat=True)
        .first()
    )
    if cart_id is None:
        raise NotFound("Cart item was not found.")

    cart = Cart.objects.select_for_update().filter(pk=cart_id, user=user).first()
    if cart is None:
        raise NotFound("Cart item was not found.")

    item = (
        CartItem.objects.select_for_update()
        .filter(pk=item_id, cart=cart)
        .first()
    )
    if item is None:
        raise NotFound("Cart item was not found.")

    return item


def add_cart_item(*, user, requested_product, quantity):
    with transaction.atomic():
        cart, _ = Cart.objects.get_or_create(user=user)
        cart = Cart.objects.select_for_update().get(pk=cart.pk)
        product = Product.objects.select_for_update().get(
            pk=requested_product.pk
        )
        _validate_product(product, quantity)

        if CartItem.objects.filter(cart=cart, product=product).exists():
            raise ProductAlreadyInCartConflict()

        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
        )
        cart.save(update_fields=["updated_at"])

    return item


def update_cart_item_quantity(*, user, item_id, quantity):
    with transaction.atomic():
        item = _get_locked_cart_item(user=user, item_id=item_id)
        product = Product.objects.select_for_update().get(pk=item.product_id)
        _validate_product(product, quantity)

        item.quantity = quantity
        item.save(update_fields=["quantity"])
        item.cart.save(update_fields=["updated_at"])

    return item


def remove_cart_item(*, user, item_id):
    with transaction.atomic():
        item = _get_locked_cart_item(user=user, item_id=item_id)
        cart = item.cart
        item.delete()
        cart.save(update_fields=["updated_at"])
