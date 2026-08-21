from rest_framework import serializers

from catalog.models import Product, ProductLabel, Label


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ["id", "name", "slug"]


class ProductLabelSerializer(serializers.ModelSerializer):
    """Показує лейбл разом із каталожним номером саме для цього товару."""

    label = LabelSerializer(read_only=True)

    class Meta:
        model = ProductLabel
        fields = ["label", "catalog_number"]


class ProductSerializer(serializers.ModelSerializer):
    product_labels = ProductLabelSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "pressing_country",
            "price",
            "stock_quantity",
            "is_active",
            "product_labels",
        ]
