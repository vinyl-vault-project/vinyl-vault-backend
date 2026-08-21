from rest_framework import viewsets, mixins

from catalog.api.serializers.artist import ArtistSerializer, ArtistDetailSerializer
from catalog.models import Artist


class ArtistViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """GET /api/artists/  і  GET /api/artists/:slug  (Artist Page)."""

    queryset = Artist.objects.all().order_by("name")
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ArtistDetailSerializer
        return ArtistSerializer
