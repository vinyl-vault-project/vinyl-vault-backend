from django.db import models

from catalog.models.artist import Artist
from catalog.models.genre import Genre
from catalog.models.style import Style
from users.models import User


class Release(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    release_year = models.PositiveIntegerField(null=True, blank=True)
    cover_url = models.URLField(blank=True)

    artists = models.ManyToManyField(Artist, related_name="releases")
    genres = models.ManyToManyField(Genre, related_name="releases", blank=True)
    styles = models.ManyToManyField(Style, related_name="releases", blank=True)

    is_album_of_week = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class SavedRelease(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_releases")
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "release")

    def __str__(self):
        return f"{self.user} -> {self.release}"
