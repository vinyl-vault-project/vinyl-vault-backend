from catalog.models import Artist, Release, Product


def make_release(title="Selected Ambient Works 85-92", artist_name="Aphex Twin", **kwargs):
    """Створює Release + Artist + активний Product одним викликом."""
    artist = Artist.objects.create(name=artist_name, slug=artist_name.lower().replace(" ", "-"))
    release = Release.objects.create(
        title=title,
        slug=title.lower().replace(" ", "-").replace(".", ""),
        release_year=kwargs.get("release_year", 1992),
    )
    release.artists.add(artist)
    if "genre" in kwargs:
        release.genres.add(kwargs["genre"])
    if "style" in kwargs:
        release.styles.add(kwargs["style"])
    Product.objects.create(
        release=release,
        pressing_country=kwargs.get("pressing_country", "UK"),
        price=kwargs.get("price", "25.00"),
        stock_quantity=kwargs.get("stock_quantity", 10),
        is_active=kwargs.get("is_active", True),
    )
    return release, artist
