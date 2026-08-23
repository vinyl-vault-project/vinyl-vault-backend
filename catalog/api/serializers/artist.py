from rest_framework import serializers

from catalog.models import Artist


class ArtistSerializer(serializers.ModelSerializer):
    """Мінімальний варіант - використовується вкладено в Release."""

    class Meta:
        model = Artist
        fields = ["id", "name", "slug", "image_url", "origin_country"]
