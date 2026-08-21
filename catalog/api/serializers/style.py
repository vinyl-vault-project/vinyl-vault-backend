from rest_framework import serializers

from catalog.models import Style


class StyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Style
        fields = ["id", "name", "slug"]
