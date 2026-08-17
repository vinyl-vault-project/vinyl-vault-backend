from decimal import Decimal

from rest_framework import serializers

from catalog.models import Artist, Product, Release
from orders.models import Cart, CartItem


class CartArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ("id", "name", "slug")
        read_only_fields = fields


class CartReleaseSerializer(serializers.ModelSerializer):
    artists = CartArtistSerializer(many=True, read_only=True)

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


class CartProductSerializer(serializers.ModelSerializer):
    release = CartReleaseSerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "release",
            "price",
            "stock_quantity",
            "is_active",
        )
        read_only_fields = fields


class CartItemReadSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "subtotal", "added_at")
        read_only_fields = fields

    def get_subtotal(self, obj: CartItem) -> str:
        subtotal = obj.product.price * obj.quantity
        return f"{subtotal:.2f}"


class CartSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "items", "total", "created_at", "updated_at")
        read_only_fields = fields

    def get_total(self, obj: Cart) -> str:
        total = sum(
            (item.product.price * item.quantity for item in obj.items.all()),
            start=Decimal("0.00"),
        )
        return f"{total:.2f}"


class CartItemCreateSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
    )
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        if "quantity" not in attrs:
            raise serializers.ValidationError({"quantity": "This field is required."})
        return attrs
