from django.contrib import admin

from orders.models import Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("added_at",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = (CartItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "added_at")
    search_fields = (
        "cart__user__email",
        "cart__user__username",
        "product__release__title",
    )
    readonly_fields = ("added_at",)
    list_select_related = ("cart__user", "product__release")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "total",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "order_number",
        "user__email",
        "email",
        "first_name",
        "last_name",
    )
    readonly_fields = ("order_number", "created_at", "updated_at")
    list_select_related = ("user",)
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "unit_price")
    search_fields = ("order__order_number", "product__release__title")
    list_select_related = ("order", "product__release")
