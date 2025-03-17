from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Category, Item


class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color', 'owner', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'item_count']
    
    def get_item_count(self, obj):
        return obj.items.count()
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_name(self, value):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            if self.instance is None:
                if Category.objects.filter(owner=request.user, name=value).exists():
                    raise serializers.ValidationError(
                        _("You already have a category with this name.")
                    )
            else:
                if (Category.objects.filter(owner=request.user, name=value)
                        .exclude(id=self.instance.id).exists()):
                    raise serializers.ValidationError(
                        _("You already have a category with this name.")
                    )
        return value


class ItemSerializer(serializers.ModelSerializer):

    category_name = serializers.StringRelatedField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    normalized_weight = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = [
            'id', 'name', 'description', 'weight', 'weight_unit', 'normalized_weight',
            'category', 'category_name', 'category_color', 'url', 'price', 'currency',
            'image', 'owner', 'is_consumable', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'category_name', 'category_color', 'normalized_weight', 
                           'created_at', 'updated_at']
    
    def get_normalized_weight(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            target_unit = request.user.weight_unit
            return obj.get_normalized_weight(target_unit)
        return obj.get_normalized_weight()
    
    def validate_category(self, value):
        request = self.context.get("request")
        if value and request and hasattr(request, "user"):
            if value.owner != request.user:
                raise serializers.ValidationError(
                    _("You can only use categories that belong to you.")
                )
        return value
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        
        if 'weight_unit' not in validated_data:
            validated_data['weight_unit'] = self.context['request'].user.weight_unit
            
        return super().create(validated_data)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        if instance.category:
            representation['category_name'] = instance.category.name
            representation['category_color'] = instance.category.color
        else:
            representation['category_name'] = None
            representation['category_color'] = None
            
        return representation