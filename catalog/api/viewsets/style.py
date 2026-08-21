from rest_framework import mixins, viewsets

from catalog.api.serializers.style import StyleSerializer
from catalog.models import Style


class StyleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Для наповнення Filters (Style)."""

    queryset = Style.objects.all().order_by("name")
    serializer_class = StyleSerializer
