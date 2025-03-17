from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsOwner
from .models import Category, Item
from .serializers import CategorySerializer, ItemSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        category = self.get_object()
        items = Item.objects.filter(category=category, owner=request.user)
        serializer = ItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)


class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_consumable', 'weight_unit']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'weight', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self):
        return Item.objects.filter(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def no_category(self, request):
        items = Item.objects.filter(owner=request.user, category__isnull=True)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        queryset = self.get_queryset()
        query = request.query_params.get('q', '')
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query)
            )
        
        category_id = request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        is_consumable = request.query_params.get('is_consumable')
        if is_consumable is not None:
            is_consumable = is_consumable.lower() == 'true'
            queryset = queryset.filter(is_consumable=is_consumable)
        
        sort_by = request.query_params.get('sort_by', 'name')
        sort_direction = '-' if request.query_params.get('desc') == 'true' else ''
        queryset = queryset.order_by(f'{sort_direction}{sort_by}')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        original = self.get_object()
        
        new_item = Item.objects.create(
            name=f"{original.name} (Copy)",
            description=original.description,
            weight=original.weight,
            weight_unit=original.weight_unit,
            category=original.category,
            url=original.url,
            price=original.price,
            currency=original.currency,
            is_consumable=original.is_consumable,
            owner=request.user
        )
        
        if original.image:
            from django.core.files.base import ContentFile
            original.image.open()
            content = ContentFile(original.image.read())
            new_item.image.save(original.image.name, content, save=True)
        
        serializer = self.get_serializer(new_item)
        return Response(serializer.data)
