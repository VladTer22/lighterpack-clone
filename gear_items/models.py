from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Category(models.Model):
    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True)
    color = models.CharField(_("color"), max_length=20, default="#3498db")  # Hex color
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["name"]
        unique_together = [["name", "owner"]]
    
    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    weight = models.DecimalField(
        _("weight"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Weight in grams or ounces (depending on user preference)")
    )
    weight_unit = models.CharField(
        _("weight unit"),
        max_length=2,
        choices=[("g", "Grams"), ("oz", "Ounces")],
        default="g",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items"
    )
    url = models.URLField(_("URL"), blank=True)
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(_("currency"), max_length=3, default="USD")
    image = models.ImageField(_("image"), upload_to="gear_images/", null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items"
    )
    is_consumable = models.BooleanField(_("is consumable"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
    def get_normalized_weight(self, target_unit=None):
        target_unit = target_unit or self.owner.weight_unit
        weight = float(self.weight)
        
        if self.weight_unit == "g" and target_unit == "oz":
            return weight / 28.35
        elif self.weight_unit == "oz" and target_unit == "g":
            return weight * 28.35
        
        return weight
