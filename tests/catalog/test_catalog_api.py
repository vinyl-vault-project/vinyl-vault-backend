from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Genre, Style, SavedRelease
from tests.catalog.factories import make_release

User = get_user_model()


class SearchEndpointTests(APITestCase):
    """Покриває Acceptance Criteria: пошук за назвою/артистом, empty state,
    фільтри, п. 9-12 ТЗ."""

    def setUp(self):
        self.electronic = Genre.objects.create(name="Electronic", slug="electronic")
        self.idm = Style.objects.create(name="IDM", slug="idm")
        self.release1, self.artist1 = make_release(
            title="Selected Ambient Works 85-92",
            artist_name="Aphex Twin",
            release_year=1992,
            genre=self.electronic,
            style=self.idm,
            price="30.00",
        )
        self.release2, self.artist2 = make_release(
            title="Endtroducing",
            artist_name="DJ Shadow",
            release_year=1996,
            price="20.00",
        )
        self.url = reverse("release-list")

    def test_search_by_album_title(self):
        response = self.client.get(self.url, {"q": "Endtroducing"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [r["title"] for r in self._results(response)]
        self.assertIn("Endtroducing", titles)
        self.assertNotIn("Selected Ambient Works 85-92", titles)

    def test_search_by_artist_name(self):
        response = self.client.get(self.url, {"q": "DJ Shadow"})
        titles = [r["title"] for r in self._results(response)]
        self.assertIn("Endtroducing", titles)

    def test_search_is_case_insensitive(self):
        response = self.client.get(self.url, {"q": "aphex twin"})
        titles = [r["title"] for r in self._results(response)]
        self.assertIn("Selected Ambient Works 85-92", titles)

    def test_search_partial_match(self):
        response = self.client.get(self.url, {"q": "shadow"})
        titles = [r["title"] for r in self._results(response)]
        self.assertIn("Endtroducing", titles)

    def test_search_no_results_returns_empty_list_not_error(self):
        response = self.client.get(self.url, {"q": "Nonexistent Album XYZ"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self._results(response)), 0)

    def test_filter_by_genre(self):
        response = self.client.get(self.url, {"genre": "electronic"})
        titles = [r["title"] for r in self._results(response)]
        self.assertIn("Selected Ambient Works 85-92", titles)
        self.assertNotIn("Endtroducing", titles)

    def test_filter_by_style(self):
        response = self.client.get(self.url, {"style": "idm"})
        titles = [r["title"] for r in self._results(response)]
        self.assertIn("Selected Ambient Works 85-92", titles)

    def test_filter_by_release_year_range(self):
        response = self.client.get(self.url, {"yearFrom": "1995", "yearTo": "2000"})
        titles = [r["title"] for r in self._results(response)]
        self.assertIn("Endtroducing", titles)
        self.assertNotIn("Selected Ambient Works 85-92", titles)

    def test_combined_filters_use_and_logic(self):
        response = self.client.get(self.url, {"genre": "electronic", "yearFrom": "1996"})
        self.assertEqual(len(self._results(response)), 0)

    def test_ordering_by_price_ascending(self):
        response = self.client.get(self.url, {"ordering": "price_asc"})
        titles = [r["title"] for r in self._results(response)]
        self.assertEqual(titles[0], "Endtroducing")

    def _results(self, response):
        return response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data


class ArtistEndpointTests(APITestCase):
    """Artist Page — додано в скоуп понад письмове ТЗ."""

    def setUp(self):
        self.release, self.artist = make_release(title="Drukqs", artist_name="Aphex Twin")

    def test_artist_detail_includes_biography_and_releases(self):
        self.artist.biography = "British electronic musician..."
        self.artist.save()
        url = reverse("artist-detail", kwargs={"slug": self.artist.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["biography"], "British electronic musician...")
        self.assertEqual(len(response.data["releases"]), 1)

    def test_artist_list_does_not_include_biography(self):
        url = reverse("artist-list")
        response = self.client.get(url)
        self.assertNotIn("biography", response.data[0])


class SavedReleaseTests(APITestCase):
    """п. 16, 25, 33 ТЗ: тільки автентифікований User, ізоляція між юзерами."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="listener", email="listener@example.com", password="pass12345"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass12345"
        )
        self.release, _ = make_release()
        self.url = reverse("saved-release-list")

    def test_guest_cannot_access_saved_albums(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_save_album(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"release_id": self.release.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SavedRelease.objects.filter(user=self.user).count(), 1)

    def test_user_cannot_save_same_release_twice(self):
        self.client.force_authenticate(user=self.user)
        SavedRelease.objects.create(user=self.user, release=self.release)
        response = self.client.post(self.url, {"release_id": self.release.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_sees_only_own_saved_albums(self):
        SavedRelease.objects.create(user=self.other_user, release=self.release)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 0)

    def test_user_can_unsave_own_album(self):
        saved = SavedRelease.objects.create(user=self.user, release=self.release)
        self.client.force_authenticate(user=self.user)
        url = reverse("saved-release-detail", kwargs={"pk": saved.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SavedRelease.objects.filter(pk=saved.pk).exists())

    def test_user_cannot_delete_another_users_saved_album(self):
        saved = SavedRelease.objects.create(user=self.other_user, release=self.release)
        self.client.force_authenticate(user=self.user)
        url = reverse("saved-release-detail", kwargs={"pk": saved.pk})
        response = self.client.delete(url)
        self.assertIn(response.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))