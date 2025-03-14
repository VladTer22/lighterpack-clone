import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from gear_items.models import Item


class GearList(models.Model):
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gear_lists"
    )
    is_public = models.BooleanField(_("public"), default=False)
    share_code = models.UUIDField(_("share code"), default=uuid.uuid4, editable=False, unique=True)
    total_weight = models.DecimalField(
        _("total weight"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Calculated total weight of all items")
    )
    weight_unit = models.CharField(
        _("weight unit"),
        max_length=2,
        choices=[("g", "Grams"), ("oz", "Ounces")],
        default="g",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("gear list")
        verbose_name_plural = _("gear lists")
        ordering = ["-updated_at"]
    
    def __str__(self):
        return self.name
    
    def calculate_total_weight(self):
        total = 0
        for list_item in self.list_items.all():
            item_weight = list_item.item.get_normalized_weight(self.weight_unit)
            item_quantity = list_item.quantity
            total += item_weight * item_quantity
        
        self.total_weight = total
        self.save(update_fields=["total_weight"])
        return total


class ListItem(models.Model):
    gear_list = models.ForeignKey(
        GearList,
        on_delete=models.CASCADE,
        related_name="list_items"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="in_lists"
    )
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    is_worn = models.BooleanField(_("worn"), default=False)
    is_packed = models.BooleanField(_("packed"), default=False)
    notes = models.TextField(_("notes"), blank=True)
    order = models.PositiveIntegerField(_("order"), default=0)
    
    class Meta:
        verbose_name = _("list item")
        verbose_name_plural = _("list items")
        ordering = ["order"]
        unique_together = [["gear_list", "item"]]
    
    def __str__(self):
        return f"{self.item.name} in {self.gear_list.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.gear_list.calculate_total_weight()
