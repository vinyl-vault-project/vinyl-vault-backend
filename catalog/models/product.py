from django.db import models

from catalog.models import Label
from catalog.models.release import Release


class Product(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="products")
    labels = models.ManyToManyField(Label, through="ProductLabel", related_name="products", blank=True)

    pressing_country = models.CharField(max_length=100)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.release.title} ({self.pressing_country})"


class ProductLabel(models.Model):
    """Проміжна модель Product <-> Label з каталожним номером конкретного видання."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_labels")
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name="product_labels")
    catalog_number = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ("product", "label")

    def __str__(self):
        return f"{self.product} — {self.label} ({self.catalog_number})"
