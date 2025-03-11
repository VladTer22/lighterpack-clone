from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    bio = models.TextField(max_length=500, blank=True)
    weight_unit = models.CharField(
        max_length=2,
        choices=[("g", "Grams"), ("oz", "Ounces")],
        default="g",
    )
    is_public_profile = models.BooleanField(default=False)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    
    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["username"]
    
    def __str__(self):
        return self.username