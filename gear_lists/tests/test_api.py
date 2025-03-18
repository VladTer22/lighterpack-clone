import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from gear_items.models import Category, Item
from gear_lists.models import GearList, ListItem

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user():
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
        weight_unit="g"
    )
    return user


@pytest.fixture
def another_user():
    user = User.objects.create_user(
        username="anotheruser",
        email="another@example.com",
        password="anotherpassword123",
        weight_unit="g"
    )
    return user


@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def test_category(test_user):
    category = Category.objects.create(
        name="Test Category",
        description="Test description",
        color="#FF5733",
        owner=test_user
    )
    return category


@pytest.fixture
def test_item(test_user, test_category):
    item = Item.objects.create(
        name="Test Item",
        description="Test item description",
        weight=100,
        weight_unit="g",
        category=test_category,
        owner=test_user
    )
    return item


@pytest.fixture
def test_gear_list(test_user):
    gear_list = GearList.objects.create(
        name="Test Gear List",
        description="Test list description",
        owner=test_user,
        weight_unit="g"
    )
    return gear_list


@pytest.fixture
def test_list_item(test_gear_list, test_item):
    list_item = ListItem.objects.create(
        gear_list=test_gear_list,
        item=test_item,
        quantity=1
    )
    return list_item


@pytest.fixture
def public_gear_list(another_user):
    gear_list = GearList.objects.create(
        name="Public Gear List",
        description="Public list description",
        owner=another_user,
        is_public=True,
        weight_unit="g"
    )
    return gear_list


@pytest.mark.django_db
class TestGearListAPI:
    
    def test_list_gear_lists(self, authenticated_client, test_gear_list, public_gear_list):
        url = reverse("gear_lists:gear_list-list")
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2
        
        list_names = [item["name"] for item in response.data]
        assert test_gear_list.name in list_names
        assert public_gear_list.name in list_names
    
    def test_create_gear_list(self, authenticated_client):
        url = reverse("gear_lists:gear_list-list")
        data = {
            "name": "New Gear List",
            "description": "New list description",
            "is_public": False,
            "weight_unit": "oz"
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == data["name"]
        assert response.data["description"] == data["description"]
        assert response.data["is_public"] == data["is_public"]
        assert response.data["weight_unit"] == data["weight_unit"]
        
        assert GearList.objects.filter(name=data["name"]).exists()
    
    def test_retrieve_gear_list(self, authenticated_client, test_gear_list, test_list_item):
        url = reverse("gear_lists:gear_list-detail", kwargs={"pk": test_gear_list.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == test_gear_list.name
        assert response.data["description"] == test_gear_list.description
        assert "list_items" in response.data
        assert len(response.data["list_items"]) == 1
        assert response.data["list_items"][0]["item"] == test_list_item.item.id
    
    def test_update_gear_list(self, authenticated_client, test_gear_list):
        url = reverse("gear_lists:gear_list-detail", kwargs={"pk": test_gear_list.id})
        data = {
            "name": "Updated Gear List",
            "description": "Updated list description",
            "is_public": True
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == data["name"]
        assert response.data["description"] == data["description"]
        assert response.data["is_public"] == data["is_public"]
        
        test_gear_list.refresh_from_db()
        assert test_gear_list.name == data["name"]
        assert test_gear_list.description == data["description"]
        assert test_gear_list.is_public == data["is_public"]
    
    def test_delete_gear_list(self, authenticated_client, test_gear_list):
        url = reverse("gear_lists:gear_list-detail", kwargs={"pk": test_gear_list.id})
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        assert not GearList.objects.filter(id=test_gear_list.id).exists()
    
    def test_add_item_to_list(self, authenticated_client, test_gear_list, test_item):
        url = reverse("gear_lists:gear_list-items", kwargs={"pk": test_gear_list.id})
        data = {
            "item": test_item.id,
            "quantity": 2,
            "is_worn": True,
            "notes": "Test notes"
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["item"] == data["item"]
        assert response.data["quantity"] == data["quantity"]
        assert response.data["is_worn"] == data["is_worn"]
        assert response.data["notes"] == data["notes"]
        
        assert ListItem.objects.filter(
            gear_list=test_gear_list,
            item=test_item
        ).exists()
    
    def test_copy_gear_list(self, authenticated_client, test_gear_list, test_list_item):
        url = reverse("gear_lists:gear_list-copy", kwargs={"pk": test_gear_list.id})
        data = {
            "name": "Copied Gear List",
            "include_items": True
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == data["name"]
        
        new_list = GearList.objects.get(name=data["name"])
        assert new_list.owner == test_gear_list.owner
        
        assert ListItem.objects.filter(gear_list=new_list).count() == 1
    
    def test_access_shared_list(self, authenticated_client, public_gear_list):
        url = reverse("gear_lists:gear_list-shared")
        data = {
            "share_code": str(public_gear_list.share_code)
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == public_gear_list.name
        assert response.data["description"] == public_gear_list.description
        assert response.data["is_public"] is True


@pytest.mark.django_db
class TestListItemAPI:
    
    def test_update_list_item(self, authenticated_client, test_list_item):
        url = reverse("gear_lists:list_item-detail", kwargs={"pk": test_list_item.id})
        data = {
            "quantity": 3,
            "is_worn": True,
            "is_packed": True,
            "notes": "Updated notes"
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["quantity"] == data["quantity"]
        assert response.data["is_worn"] == data["is_worn"]
        assert response.data["is_packed"] == data["is_packed"]
        assert response.data["notes"] == data["notes"]
        
        test_list_item.refresh_from_db()
        assert test_list_item.quantity == data["quantity"]
        assert test_list_item.is_worn == data["is_worn"]
        assert test_list_item.is_packed == data["is_packed"]
        assert test_list_item.notes == data["notes"]
    
    def test_delete_list_item(self, authenticated_client, test_list_item):
        url = reverse("gear_lists:list_item-detail", kwargs={"pk": test_list_item.id})
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        assert not ListItem.objects.filter(id=test_list_item.id).exists()
    
    def test_toggle_packed(self, authenticated_client, test_list_item):
        url = reverse("gear_lists:list_item-toggle-packed", kwargs={"pk": test_list_item.id})
        initial_is_packed = test_list_item.is_packed
        
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_packed"] != initial_is_packed
        
        test_list_item.refresh_from_db()
        assert test_list_item.is_packed != initial_is_packed
    
    def test_reorder_list_items(self, authenticated_client, test_gear_list, test_list_item, test_item):
        second_item = Item.objects.create(
            name="Second Item",
            description="Second item description",
            weight=200,
            weight_unit="g",
            owner=test_gear_list.owner
        )
        second_list_item = ListItem.objects.create(
            gear_list=test_gear_list,
            item=second_item,
            quantity=1,
            order=1
        )
        
        url = reverse("gear_lists:list_item-reorder")
        data = {
            "items_order": [second_list_item.id, test_list_item.id]
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        
        test_list_item.refresh_from_db()
        second_list_item.refresh_from_db()
        assert test_list_item.order == 1
        assert second_list_item.order == 0