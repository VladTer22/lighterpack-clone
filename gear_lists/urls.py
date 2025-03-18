from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GearListViewSet, ListItemViewSet

router = DefaultRouter()
router.register(r'lists', GearListViewSet, basename='gear_list')
router.register(r'list-items', ListItemViewSet, basename='list_item')

app_name = 'gear_lists'

urlpatterns = [
    path('', include(router.urls)),
]