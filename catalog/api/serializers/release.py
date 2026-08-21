from rest_framework import serializers

from catalog.api.serializers.artist import ArtistSerializer
from catalog.api.serializers.genre import GenreSerializer
from catalog.api.serializers.product import ProductSerializer
from catalog.api.serializers.style import StyleSerializer
from catalog.api.serializers.track import TrackSerializer
from catalog.models import Release, SavedRelease


class ReleaseListSerializer(serializers.ModelSerializer):
    """Для сітки каталогу / Search Results (AlbumCard): cover, artist,
    title, release_year, price. Мінімум полів - швидкий список."""

    artists = ArtistSerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = Release
        fields = ["id", "slug", "title", "cover_url", "release_year", "artists", "price"]

    def get_price(self, obj):
        # ціна активного товару; якщо кілька видань - беремо найдешевше активне
        product = obj.products.filter(is_active=True).order_by("price").first()
        return product.price if product else None


class ReleaseDetailSerializer(serializers.ModelSerializer):
    """Для Album Page: усі характеристики релізу + треклист + товар(и)."""

    artists = ArtistSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    styles = StyleSerializer(many=True, read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Release
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "release_year",
            "cover_url",
            "artists",
            "genres",
            "styles",
            "tracks",
            "products",
            "created_at",
        ]


class SavedReleaseSerializer(serializers.ModelSerializer):
    release = ReleaseListSerializer(read_only=True)
    release_id = serializers.PrimaryKeyRelatedField(
        queryset=Release.objects.all(), source="release", write_only=True
    )

    class Meta:
        model = SavedRelease
        fields = ["id", "release", "release_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
