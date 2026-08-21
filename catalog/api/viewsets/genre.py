from rest_framework import mixins, viewsets

from catalog.api.serializers.genre import GenreSerializer
from catalog.models import Genre


class GenreViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Для наповнення Filters (Genre)."""

    queryset = Genre.objects.all().order_by("name")
    serializer_class = GenreSerializer
