"""
Використання:
    docker-compose exec backend python manage.py import_artists data/artists.csv

Очікувані колонки (tab- або comma-separated, автовизначення):
artist_id, artist_name, artist_origin_country, artist_image_url, artist_biography

Прив'язка до вже імпортованих Release відбувається за іменем артиста
(Artist.name), яке має точно збігатися з колонкою "artist" в albums.csv.
"""

import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Artist


class Command(BaseCommand):
    help = "Імпортує/доповнює артистів з artists.csv (біографія, фото, країна)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Шлях до artists.csv")

    def handle(self, *args, **options):
        path = options["csv_path"]
        created, updated, skipped = 0, 0, 0

        with open(path, newline="", encoding="utf-8") as f:
            sample = f.read(2048)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters="\t,")
            except csv.Error:
                dialect = csv.excel
            reader = csv.DictReader(f, dialect=dialect)

            for row in reader:
                name = (row.get("artist_name") or "").strip()
                if not name:
                    skipped += 1
                    continue

                artist, was_created = Artist.objects.update_or_create(
                    name=name,
                    defaults={
                        "slug": slugify(name),
                        "origin_country": (row.get("artist_origin_country") or "").strip(),
                        "image_url": (row.get("artist_image_url") or "").strip(),
                        "biography": (row.get("artist_biography") or "").strip(),
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Створено: {created}, оновлено: {updated}, пропущено: {skipped}"
            )
        )