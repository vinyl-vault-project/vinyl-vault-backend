from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from catalog.api.serializers.release import ReleaseListSerializer
from catalog.models import Artist


class ArtistDetailSerializer(serializers.ModelSerializer):
    releases = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = ["id", "name", "slug", "image_url", "biography", "origin_country", "releases"]

    @extend_schema_field(ReleaseListSerializer(many=True))
    def get_releases(self, obj):
        # імпорт ТУТ, всередині методу - розриває цикл, бо виконується
        # вже після того, як обидва модулі повністю завантажені
        releases = obj.releases.all().order_by("-release_year")
        return ReleaseListSerializer(releases, many=True, context=self.context).data
