from django.db import models

class Artist(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    image_url = models.URLField(blank=True)
    biography = models.TextField(blank=True)
    origin_country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name
