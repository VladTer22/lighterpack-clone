from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from gear_items.models import Item
from gear_items.serializers import ItemSerializer
from .models import GearList, ListItem


class ListItemSerializer(serializers.ModelSerializer):
    item_details = ItemSerializer(source='item', read_only=True)
    total_weight = serializers.SerializerMethodField()
    
    class Meta:
        model = ListItem
        fields = [
            'id', 'gear_list', 'item', 'item_details', 'quantity', 
            'is_worn', 'is_packed', 'notes', 'order', 'total_weight'
        ]
        read_only_fields = ['id', 'total_weight']
    
    def get_total_weight(self, obj):
        target_unit = obj.gear_list.weight_unit
        item_weight = obj.item.get_normalized_weight(target_unit)
        return round(item_weight * obj.quantity, 2)
    
    def validate_item(self, value):
        request = self.context.get("request")
        if value and request and hasattr(request, "user"):
            if value.owner != request.user:
                raise serializers.ValidationError(
                    _("You can only use items that belong to you.")
                )
        return value
    
    def validate_gear_list(self, value):
        request = self.context.get("request")
        if value and request and hasattr(request, "user"):
            if value.owner != request.user:
                raise serializers.ValidationError(
                    _("You can only add items to lists that belong to you.")
                )
        return value
    
    def validate(self, attrs):
        gear_list = attrs.get('gear_list') or self.instance.gear_list if self.instance else None
        item = attrs.get('item') or self.instance.item if self.instance else None
        
        if gear_list and item:
            if not self.instance:
                if ListItem.objects.filter(gear_list=gear_list, item=item).exists():
                    raise serializers.ValidationError(
                        _("This item is already in the list.")
                    )
        
        return attrs


class GearListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GearList
        fields = [
            'id', 'name', 'description', 'owner', 'is_public', 'share_code',
            'total_weight', 'weight_unit', 'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'share_code', 'total_weight', 'items_count', 
                           'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        return obj.list_items.count()
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        
        if 'weight_unit' not in validated_data:
            validated_data['weight_unit'] = self.context['request'].user.weight_unit
            
        return super().create(validated_data)


class GearListDetailSerializer(GearListSerializer):
    list_items = ListItemSerializer(many=True, read_only=True)
    total_worn_weight = serializers.SerializerMethodField()
    total_base_weight = serializers.SerializerMethodField()
    total_consumables_weight = serializers.SerializerMethodField()
    
    class Meta(GearListSerializer.Meta):
        fields = GearListSerializer.Meta.fields + [
            'list_items', 'total_worn_weight', 'total_base_weight', 'total_consumables_weight'
        ]
    
    def get_total_worn_weight(self, obj):
        total = 0
        for list_item in obj.list_items.filter(is_worn=True):
            item_weight = list_item.item.get_normalized_weight(obj.weight_unit)
            total += item_weight * list_item.quantity
        return round(total, 2)
    
    def get_total_base_weight(self, obj):
        total = 0
        for list_item in obj.list_items.filter(is_worn=False):
            item = list_item.item
            if not item.is_consumable:
                item_weight = item.get_normalized_weight(obj.weight_unit)
                total += item_weight * list_item.quantity
        return round(total, 2)
    
    def get_total_consumables_weight(self, obj):
        total = 0
        for list_item in obj.list_items.all():
            item = list_item.item
            if item.is_consumable:
                item_weight = item.get_normalized_weight(obj.weight_unit)
                total += item_weight * list_item.quantity
        return round(total, 2)


class GearListCopySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    include_items = serializers.BooleanField(default=True)
    
    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("Name cannot be empty."))
        return value


class GearListShareSerializer(serializers.Serializer):
    share_code = serializers.UUIDField(required=True)