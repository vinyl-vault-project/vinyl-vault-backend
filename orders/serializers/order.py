from decimal import Decimal

from rest_framework import serializers

from catalog.models import Artist, Label, Product, Release
from orders.models import Order, OrderItem


class OrderArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ("id", "name", "slug")
        read_only_fields = fields


class OrderLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ("id", "name", "slug")
        read_only_fields = fields


class OrderListReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = ("id", "title", "cover_url")
        read_only_fields = fields


class OrderListProductSerializer(serializers.ModelSerializer):
    release = OrderListReleaseSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ("id", "release")
        read_only_fields = fields


class OrderListItemSerializer(serializers.ModelSerializer):
    product = OrderListProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "quantity")
        read_only_fields = fields


class OrderReleaseSerializer(serializers.ModelSerializer):
    artists = OrderArtistSerializer(many=True, read_only=True)

    class Meta:
        model = Release
        fields = (
            "id",
            "slug",
            "title",
            "cover_url",
            "release_year",
            "artists",
        )
        read_only_fields = fields


class OrderProductSerializer(serializers.ModelSerializer):
    release = OrderReleaseSerializer(read_only=True)
    labels = OrderLabelSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ("id", "release", "labels")
        read_only_fields = fields


class OrderCheckoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "city",
            "shipping_address",
            "postal_code",
            "country",
        )


class OrderItemReadSerializer(serializers.ModelSerializer):
    product = OrderProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "quantity", "unit_price", "subtotal")
        read_only_fields = fields

    def get_subtotal(self, obj: OrderItem) -> str:
        subtotal = obj.unit_price * obj.quantity
        return f"{subtotal:.2f}"


class OrderListSerializer(serializers.ModelSerializer):
    items = OrderListItemSerializer(many=True, read_only=True)
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "status",
            "items",
            "total_quantity",
            "total",
            "created_at",
        )
        read_only_fields = fields

    def get_total_quantity(self, obj: Order) -> int:
        return sum(item.quantity for item in obj.items.all())


class OrderDetailSerializer(serializers.ModelSerializer):
    checkout_data = OrderCheckoutSerializer(source="*", read_only=True)
    items = OrderItemReadSerializer(many=True, read_only=True)
    line_items_count = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "status",
            "items",
            "line_items_count",
            "subtotal",
            "total",
            "checkout_data",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_line_items_count(self, obj: Order) -> int:
        return len(obj.items.all())

    def get_subtotal(self, obj: Order) -> str:
        subtotal = sum(
            (item.unit_price * item.quantity for item in obj.items.all()),
            start=Decimal("0.00"),
        )
        return f"{subtotal:.2f}"
