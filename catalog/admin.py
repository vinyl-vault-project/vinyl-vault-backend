from django.contrib import admin

from .models import (
    Genre,
    Style,
    Label,
    Artist,
    Release,
    Track,
    Product,
    SavedRelease, ProductLabel,
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "origin_country")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class TrackInline(admin.TabularInline):
    model = Track
    extra = 1
    ordering = ("side", "position")


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ("title", "release_year", "is_album_of_week", "created_at")
    list_filter = ("is_album_of_week", "genres", "styles", "release_year")
    search_fields = ("title", "artists__name")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("artists", "genres", "styles")
    inlines = [TrackInline]


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ("release", "side", "position", "title", "duration_seconds")
    list_filter = ("side",)
    search_fields = ("title", "release__title")
    ordering = ("release", "side", "position")


class ProductLabelInline(admin.TabularInline):
    model = ProductLabel
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("release", "pressing_country", "price", "stock_quantity", "is_active")
    list_filter = ("is_active", "pressing_country")
    search_fields = ("release__title",)
    inlines = [ProductLabelInline]


@admin.register(SavedRelease)
class SavedReleaseAdmin(admin.ModelAdmin):
    list_display = ("user", "release", "created_at")
    search_fields = ("user__username", "release__title")
