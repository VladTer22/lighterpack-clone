from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_public_profile")
    list_filter = ("is_staff", "is_superuser", "is_active", "is_public_profile")
    search_fields = ("username", "email", "first_name", "last_name")
    
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "bio", "profile_picture")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Settings"), {"fields": ("weight_unit", "is_public_profile")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
