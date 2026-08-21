"""
Використання:
    docker-compose exec backend python manage.py import_albums data/albums.csv

Очікувані колонки CSV (як у датасеті vinyl_store_albums.csv, вкладка "albums"):
album_id, artist_id, artist, artist_image_url, album, year, pressing_country,
genre, style, price, stock_quantity, label, description, cover_url

genre і style можуть містити кілька значень через кому ("Electronic, Hip Hop") —
команда розбиває їх і створює/використовує окремі Genre/Style записи для кожного.
"""

import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Genre, Style, Label, Artist, Release, Product


class Command(BaseCommand):
    help = "Імпортує альбоми з CSV (експорт вкладки 'albums' датасету) у каталог."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Шлях до albums.csv")
        parser.add_argument(
            "--stock-fallback",
            type=int,
            default=0,
            help="stock_quantity, якщо в рядку CSV значення порожнє/некоректне",
        )

    def handle(self, *args, **options):
        path = options["csv_path"]
        created, updated, skipped = 0, 0, 0

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    release, was_created = self._import_row(row, options["stock_fallback"])
                except Exception as exc:  # не рвемо весь імпорт через один битий рядок
                    self.stderr.write(
                        self.style.WARNING(
                            f"Пропущено рядок album_id={row.get('album_id')}: {exc}"
                        )
                    )
                    skipped += 1
                    continue

                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Створено: {created}, оновлено: {updated}, пропущено: {skipped}"
            )
        )

    def _import_row(self, row, stock_fallback):
        artist_name = row["artist"].strip()
        artist, _ = Artist.objects.get_or_create(
            name=artist_name,
            defaults={
                "slug": slugify(artist_name),
                "image_url": row.get("artist_image_url", "").strip(),
            },
        )
        # якщо артист вже існував без фото — доповнюємо
        if not artist.image_url and row.get("artist_image_url"):
            artist.image_url = row["artist_image_url"].strip()
            artist.save(update_fields=["image_url"])

        label = None
        label_name = row.get("label", "").strip()
        if label_name:
            label, _ = Label.objects.get_or_create(
                name=label_name, defaults={"slug": slugify(label_name)}
            )

        title = row["album"].strip()
        release, release_created = Release.objects.get_or_create(
            title=title,
            slug=slugify(f"{title}-{row.get('year', '')}"),
            defaults={
                "description": row.get("description", "").strip(),
                "release_year": self._to_int(row.get("year")),
                "cover_url": row.get("cover_url", "").strip(),
            },
        )
        release.artists.add(artist)

        for genre_name in self._split_multi(row.get("genre", "")):
            genre, _ = Genre.objects.get_or_create(
                name=genre_name, defaults={"slug": slugify(genre_name)}
            )
            release.genres.add(genre)

        for style_name in self._split_multi(row.get("style", "")):
            style, _ = Style.objects.get_or_create(
                name=style_name, defaults={"slug": slugify(style_name)}
            )
            release.styles.add(style)

        price = row.get("price", "0").strip() or "0"
        stock = self._to_int(row.get("stock_quantity")) or stock_fallback
        pressing_country = row.get("pressing_country", "").strip()

        product, _ = Product.objects.update_or_create(
            release=release,
            pressing_country=pressing_country,
            defaults={
                "price": price,
                "stock_quantity": stock,
                "is_active": True,
            },
        )

        if label:
            from catalog.models import ProductLabel

            ProductLabel.objects.get_or_create(product=product, label=label)

        return release, release_created

    @staticmethod
    def _split_multi(value):
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]

    @staticmethod
    def _to_int(value):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None