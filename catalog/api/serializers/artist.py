from rest_framework import serializers

from catalog.models import Artist


class ArtistSerializer(serializers.ModelSerializer):
    """Мінімальний варіант - використовується вкладено в Release."""

    class Meta:
        model = Artist
        fields = ["id", "name", "slug", "image_url", "origin_country"]

class ArtistDetailSerializer(serializers.ModelSerializer):
    releases = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = ["id", "name", "slug", "image_url", "biography", "origin_country", "releases"]

    def get_releases(self, obj):
        # імпорт ТУТ, всередині методу - розриває цикл, бо виконується
        # вже після того, як обидва модулі повністю завантажені
        from catalog.api.serializers.release import ReleaseListSerializer

        releases = obj.releases.all().order_by("-release_year")
        return ReleaseListSerializer(releases, many=True, context=self.context).data
