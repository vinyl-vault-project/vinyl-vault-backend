app_name = "catalog"

from rest_framework.routers import DefaultRouter

from catalog.api.viewsets.artist import ArtistViewSet
from catalog.api.viewsets.genre import GenreViewSet
from catalog.api.viewsets.release import ReleaseViewSet, SavedReleaseViewSet
from catalog.api.viewsets.style import StyleViewSet

router = DefaultRouter()
router.register("releases", ReleaseViewSet, basename="release")
router.register("genres", GenreViewSet, basename="genre")
router.register("styles", StyleViewSet, basename="style")
router.register("artists", ArtistViewSet, basename="artist")
router.register("saved", SavedReleaseViewSet, basename="saved-release")

urlpatterns = router.urls
