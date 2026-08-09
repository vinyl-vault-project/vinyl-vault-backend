from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "id",
        "email",
        "username",
        "is_staff",
        "is_active",
    )
    ordering = ("email",)
    search_fields = ("email", "username")

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Contact information",
            {
                "fields": (
                    "phone",
                    "address",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
