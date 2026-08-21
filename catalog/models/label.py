from django.db import models


class Label(models.Model):
    """Музичний лейбл / імпринт (п. 28.5 ТЗ)."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def __str__(self):
        return self.name
