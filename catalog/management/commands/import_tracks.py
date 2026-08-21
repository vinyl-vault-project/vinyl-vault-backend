"""
Використання:
    docker-compose exec backend python manage.py import_tracks data/albums.csv data/tracks.csv

Запускати ПІСЛЯ import_albums (Release-и мають вже існувати в БД).

tracks.csv колонки: track_id, album_id, side, position, track_name, duration, audio_preview_url
duration очікується у форматі mm:ss (наприклад "04:22") — конвертується в секунди.

Прив'язка до Release відбувається через album_id → title+year з albums.csv →
той самий slug, який генерує Release.save() (slugify(f"{title}-{year}")).
Це не вимагає жодного додаткового поля в моделі Release.
"""

import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Release, Track


class Command(BaseCommand):
    help = "Імпортує треки з tracks.csv, зіставляючи album_id з Release через albums.csv."

    def add_arguments(self, parser):
        parser.add_argument("albums_csv_path", type=str, help="Шлях до albums.csv")
        parser.add_argument("tracks_csv_path", type=str, help="Шлях до tracks.csv")

    def handle(self, *args, **options):
        album_id_to_slug = self._build_album_id_map(options["albums_csv_path"])

        created, updated, skipped = 0, 0, 0

        with open(options["tracks_csv_path"], newline="", encoding="utf-8") as f:
            reader = self._reader(f)

            for row in reader:
                album_id = (row.get("album_id") or "").strip()
                slug = album_id_to_slug.get(album_id)

                if not slug:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Пропущено track_id={row.get('track_id')}: "
                            f"album_id={album_id} не знайдено в albums.csv"
                        )
                    )
                    skipped += 1
                    continue

                try:
                    release = Release.objects.get(slug=slug)
                except Release.DoesNotExist:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Пропущено track_id={row.get('track_id')}: "
                            f"Release зі slug='{slug}' не знайдено в БД "
                            f"(запустіть import_albums першим)"
                        )
                    )
                    skipped += 1
                    continue

                side = (row.get("side") or "").strip().upper()
                position = self._to_int(row.get("position")) or 1
                title = (row.get("track_name") or "").strip()
                duration_seconds = self._parse_duration(row.get("duration"))
                audio_url = (row.get("audio_preview_url") or "").strip()

                track, was_created = Track.objects.update_or_create(
                    release=release,
                    side=side,
                    position=position,
                    defaults={
                        "title": title,
                        "duration_seconds": duration_seconds,
                        "audio_preview_url": audio_url,
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

    def _build_album_id_map(self, albums_csv_path):
        """album_id -> slug, обчислений так само, як у Release.save()."""
        mapping = {}
        with open(albums_csv_path, newline="", encoding="utf-8") as f:
            reader = self._reader(f)
            for row in reader:
                album_id = (row.get("album_id") or "").strip()
                title = (row.get("album") or "").strip()
                year = (row.get("year") or "").strip()
                mapping[album_id] = slugify(f"{title}-{year}")
        return mapping

    @staticmethod
    def _reader(fileobj):
        sample = fileobj.read(2048)
        fileobj.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="\t,")
        except csv.Error:
            dialect = csv.excel
        return csv.DictReader(fileobj, dialect=dialect)

    @staticmethod
    def _to_int(value):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_duration(value):
        """'04:22' -> 262 (секунди). Повертає None, якщо формат незрозумілий."""
        if not value:
            return None
        parts = str(value).strip().split(":")
        try:
            parts = [int(p) for p in parts]
        except ValueError:
            return None

        if len(parts) == 2:
            minutes, seconds = parts
            return minutes * 60 + seconds
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return hours * 3600 + minutes * 60 + seconds
        return None