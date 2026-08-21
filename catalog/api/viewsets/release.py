from django.db.models import Min, Q
from rest_framework import permissions, viewsets, mixins
from rest_framework.exceptions import PermissionDenied

from catalog.api.pagination import ReleasePagination
from catalog.api.serializers.release import SavedReleaseSerializer, ReleaseListSerializer, ReleaseDetailSerializer
from catalog.models import SavedRelease, Release


class ReleaseViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """GET /api/search  (список + пошук + фільтри)
    GET /api/albums/:slug  (Album Page)."""

    lookup_field = "slug"
    pagination_class = ReleasePagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ReleaseDetailSerializer
        return ReleaseListSerializer

    def get_queryset(self):
        qs = (
            Release.objects.all()
            .prefetch_related("artists", "genres", "styles", "products", "tracks")
            .distinct()
        )
        params = self.request.query_params

        # --- Пошук за назвою альбому АБО артистом (п. 9) ---
        search = params.get("search", "").strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(artists__name__icontains=search))

        # --- Featured Artist / прямий фільтр за артистом (slug) ---
        artist = params.get("artist")
        if artist:
            qs = qs.filter(artists__slug=artist)

        # --- Genre: кілька значень через кому = OR (п. 11) ---
        genres = params.get("genre")
        if genres:
            qs = qs.filter(genres__slug__in=genres.split(","))

        # --- Style: кілька значень через кому = OR ---
        styles = params.get("style")
        if styles:
            qs = qs.filter(styles__slug__in=styles.split(","))

        # --- Country: фільтрується через pressing_country на Product ---
        country = params.get("country")
        if country:
            qs = qs.filter(products__pressing_country__in=country.split(","))

        # --- Release Year: діапазон ---
        year_from = params.get("year_from")
        year_to = params.get("year_to")
        if year_from:
            qs = qs.filter(release_year__gte=year_from)
        if year_to:
            qs = qs.filter(release_year__lte=year_to)

        # --- Сортування ---
        ordering = params.get("ordering")
        if ordering == "title_asc":
            qs = qs.order_by("title")
        elif ordering == "title_desc":
            qs = qs.order_by("-title")
        elif ordering in ("price_asc", "price_desc"):
            qs = qs.annotate(min_price=Min("products__price"))
            qs = qs.order_by("min_price" if ordering == "price_asc" else "-min_price")

        return qs


class SavedReleaseViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """GET /api/account/saved
    POST /api/saved/:releaseId  (release_id у тілі запиту)
    DELETE /api/saved/:releaseId"""

    serializer_class = SavedReleaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # користувач бачить лише власні збережені альбоми
        return SavedRelease.objects.filter(user=self.request.user).select_related("release")

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("Не можна видаляти чужі збережені альбоми.")
        instance.delete()
