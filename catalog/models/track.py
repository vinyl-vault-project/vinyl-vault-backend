from django.db import models

from catalog.models.release import Release


class Track(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="tracks")
    side = models.CharField(max_length=2, blank=True)
    position = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    audio_preview_url = models.URLField(max_length=1000, blank=True)

    class Meta:
        unique_together = ("release", "side", "position")
        ordering = ["side", "position"]

    def __str__(self):
        return f"{self.side}{self.position}. {self.title}"
