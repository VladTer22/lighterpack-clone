import uuid
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.exceptions import ResourceConflictError
from core.permissions import IsOwner, IsOwnerOrPublic
from .models import GearList, ListItem
from .serializers import (
    GearListCopySerializer,
    GearListDetailSerializer,
    GearListSerializer,
    GearListShareSerializer,
    ListItemSerializer,
)


class GearListViewSet(viewsets.ModelViewSet):
    serializer_class = GearListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrPublic]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at', 'total_weight']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        user = self.request.user
        
        share_code = self.request.query_params.get('share_code')
        if self.action == 'retrieve' and share_code:
            try:
                uuid_obj = uuid.UUID(share_code)
                return GearList.objects.filter(
                    Q(owner=user) | Q(is_public=True) | Q(share_code=uuid_obj)
                )
            except (ValueError, TypeError):
                pass
        
        return GearList.objects.filter(
            Q(owner=user) | Q(is_public=True)
        )
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'items']:
            return GearListDetailSerializer
        return GearListSerializer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get', 'post'])
    def items(self, request, pk=None):
        gear_list = self.get_object()
        
        if request.method == 'GET':
            serializer = self.get_serializer(gear_list)
            return Response(serializer.data)
        
        item_data = request.data.copy()
        item_data['gear_list'] = gear_list.id
        
        serializer = ListItemSerializer(data=item_data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            gear_list.calculate_total_weight()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], serializer_class=GearListCopySerializer)
    def copy(self, request, pk=None):
        original = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            new_list = GearList.objects.create(
                name=serializer.validated_data['name'],
                description=original.description,
                owner=request.user,
                is_public=False,
                weight_unit=request.user.weight_unit
            )
            
            if serializer.validated_data.get('include_items', True):
                for list_item in original.list_items.all():
                    if list_item.item.owner == request.user:
                        ListItem.objects.create(
                            gear_list=new_list,
                            item=list_item.item,
                            quantity=list_item.quantity,
                            is_worn=list_item.is_worn,
                            is_packed=list_item.is_packed,
                            notes=list_item.notes,
                            order=list_item.order
                        )
            
            new_list.calculate_total_weight()
            
            return Response(
                GearListSerializer(new_list, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], serializer_class=GearListShareSerializer, permission_classes=[permissions.IsAuthenticated])
    def shared(self, request):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            share_code = serializer.validated_data['share_code']
            gear_list = get_object_or_404(GearList, share_code=share_code)
            
            detail_serializer = GearListDetailSerializer(gear_list, context={'request': request})
            return Response(detail_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListItemViewSet(viewsets.ModelViewSet):
    serializer_class = ListItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return ListItem.objects.filter(gear_list__owner=self.request.user)
    
    def perform_create(self, serializer):
        gear_list = serializer.validated_data.get('gear_list')
        item = serializer.validated_data.get('item')
        
        if ListItem.objects.filter(gear_list=gear_list, item=item).exists():
            raise ResourceConflictError(_("This item is already in the list."))
        
        list_item = serializer.save()
        
        list_item.gear_list.calculate_total_weight()
    
    def perform_update(self, serializer):

        list_item = serializer.save()
        
        list_item.gear_list.calculate_total_weight()
    
    def perform_destroy(self, instance):
        gear_list = instance.gear_list
        instance.delete()
        
        gear_list.calculate_total_weight()
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        items_order = request.data.get('items_order', [])
        if not items_order or not isinstance(items_order, list):
            return Response(
                {"detail": _("Invalid data format. Expected a list of item IDs.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not items_order:
            return Response(
                {"detail": _("No items provided.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            first_item = ListItem.objects.get(id=items_order[0])
            gear_list = first_item.gear_list
            
            if gear_list.owner != request.user:
                return Response(
                    {"detail": _("You don't have permission to reorder this list.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            for index, item_id in enumerate(items_order):
                try:
                    list_item = ListItem.objects.get(id=item_id, gear_list=gear_list)
                    list_item.order = index
                    list_item.save(update_fields=['order'])
                except ListItem.DoesNotExist:
                    pass
            
            return Response({"detail": _("Items reordered successfully.")})
            
        except ListItem.DoesNotExist:
            return Response(
                {"detail": _("Item not found.")},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def toggle_packed(self, request, pk=None):
        list_item = self.get_object()
        list_item.is_packed = not list_item.is_packed
        list_item.save(update_fields=['is_packed'])
        
        return Response(
            ListItemSerializer(list_item, context={'request': request}).data
        )
