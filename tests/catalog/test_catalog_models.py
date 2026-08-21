from rest_framework.test import APITestCase

from catalog.models import Genre, Style, Artist, Release, Track, Product

from .factories import make_release


class GenreStyleModelTests(APITestCase):
    """Базові перевірки довідників — п. 28.3/28.4 ТЗ."""

    def test_genre_str_returns_name(self):
        genre = Genre.objects.create(name="Electronic", slug="electronic")
        self.assertEqual(str(genre), "Electronic")

    def test_style_str_returns_name(self):
        style = Style.objects.create(name="IDM", slug="idm")
        self.assertEqual(str(style), "IDM")

    def test_genre_slug_must_be_unique(self):
        Genre.objects.create(name="Rock", slug="rock")
        with self.assertRaises(Exception):
            Genre.objects.create(name="Rock 2", slug="rock")


class ReleaseModelTests(APITestCase):
    def test_release_str_returns_title(self):
        release, _ = make_release(title="Endtroducing")
        self.assertEqual(str(release), "Endtroducing")

    def test_release_can_have_multiple_artists(self):
        release, artist1 = make_release(title="Collab Album")
        artist2 = Artist.objects.create(name="Second Artist", slug="second-artist")
        release.artists.add(artist2)
        self.assertEqual(release.artists.count(), 2)


class TrackModelTests(APITestCase):
    def test_track_unique_together_side_position(self):
        release, _ = make_release()
        Track.objects.create(release=release, side="A", position=1, title="Xtal")
        with self.assertRaises(Exception):
            Track.objects.create(release=release, side="A", position=1, title="Duplicate")

    def test_tracks_ordered_by_side_then_position(self):
        release, _ = make_release()
        Track.objects.create(release=release, side="B", position=1, title="B1")
        Track.objects.create(release=release, side="A", position=2, title="A2")
        Track.objects.create(release=release, side="A", position=1, title="A1")
        titles = list(release.tracks.values_list("title", flat=True))
        self.assertEqual(titles, ["A1", "A2", "B1"])
