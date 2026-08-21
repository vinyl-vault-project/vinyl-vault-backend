from django.db import models

from catalog.models.release import Release


class Track(models.Model):
    class Side(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"
        E = "E", "E"
        F = "F", "F"
        G = "G", "G"
        H = "H", "H"

    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="tracks")
    side = models.CharField(max_length=1, choices=Side.choices, blank=True)
    position = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    audio_preview_url = models.URLField(max_length=1000, blank=True)

    class Meta:
        unique_together = ("release", "side", "position")
        ordering = ["side", "position"]

    def __str__(self):
        return f"{self.side}{self.position}. {self.title}"
