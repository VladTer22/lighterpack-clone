import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from gear_items.models import Category, Item

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


@pytest.mark.django_db
class TestCategoryAPI:
    
    def test_list_categories(self, authenticated_client, test_category):
        url = reverse("gear_items:category-list")
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["name"] == test_category.name
    
    def test_create_category(self, authenticated_client):
        url = reverse("gear_items:category-list")
        data = {
            "name": "New Category",
            "description": "New description",
            "color": "#3498DB"
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == data["name"]
        assert response.data["description"] == data["description"]
        assert response.data["color"] == data["color"]
        
        assert Category.objects.filter(name=data["name"]).exists()
    
    def test_retrieve_category(self, authenticated_client, test_category):
        url = reverse("gear_items:category-detail", kwargs={"pk": test_category.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == test_category.name
        assert response.data["description"] == test_category.description
        assert response.data["color"] == test_category.color
    
    def test_update_category(self, authenticated_client, test_category):
        url = reverse("gear_items:category-detail", kwargs={"pk": test_category.id})
        data = {
            "name": "Updated Category",
            "description": "Updated description",
            "color": "#2ECC71"
        }
        
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == data["name"]
        assert response.data["description"] == data["description"]
        assert response.data["color"] == data["color"]
        
        test_category.refresh_from_db()
        assert test_category.name == data["name"]
        assert test_category.description == data["description"]
        assert test_category.color == data["color"]
    
    def test_delete_category(self, authenticated_client, test_category):
        url = reverse("gear_items:category-detail", kwargs={"pk": test_category.id})
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        assert not Category.objects.filter(id=test_category.id).exists()
    
    def test_get_category_items(self, authenticated_client, test_category, test_item):
        url = reverse("gear_items:category-items", kwargs={"pk": test_category.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["name"] == test_item.name


@pytest.mark.django_db
class TestItemAPI:
    
    def test_list_items(self, authenticated_client, test_item):
        url = reverse("gear_items:item-list")
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["name"] == test_item.name
    
    def test_create_item(self, authenticated_client, test_category):
        url = reverse("gear_items:item-list")
        data = {
            "name": "New Item",
            "description": "New item description",
            "weight": 200,
            "weight_unit": "g",
            "category": test_category.id,
            "is_consumable": True
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == data["name"]
        assert response.data["description"] == data["description"]
        assert float(response.data["weight"]) == data["weight"]
        assert response.data["weight_unit"] == data["weight_unit"]
        assert response.data["category"] == data["category"]
        assert response.data["is_consumable"] == data["is_consumable"]
        
        assert Item.objects.filter(name=data["name"]).exists()
    
    def test_retrieve_item(self, authenticated_client, test_item):
        url = reverse("gear_items:item-detail", kwargs={"pk": test_item.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == test_item.name
        assert response.data["description"] == test_item.description
        assert float(response.data["weight"]) == test_item.weight
        assert response.data["weight_unit"] == test_item.weight_unit
        assert response.data["category"] == test_item.category.id
    
    def test_update_item(self, authenticated_client, test_item):
        url = reverse("gear_items:item-detail", kwargs={"pk": test_item.id})
        data = {
            "name": "Updated Item",
            "description": "Updated item description",
            "weight": 150,
            "is_consumable": True
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == data["name"]
        assert response.data["description"] == data["description"]
        assert float(response.data["weight"]) == data["weight"]
        assert response.data["is_consumable"] == data["is_consumable"]
        
        test_item.refresh_from_db()
        assert test_item.name == data["name"]
        assert test_item.description == data["description"]
        assert float(test_item.weight) == data["weight"]
        assert test_item.is_consumable == data["is_consumable"]
    
    def test_delete_item(self, authenticated_client, test_item):
        url = reverse("gear_items:item-detail", kwargs={"pk": test_item.id})
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        assert not Item.objects.filter(id=test_item.id).exists()
    
    def test_duplicate_item(self, authenticated_client, test_item):
        url = reverse("gear_items:item-duplicate", kwargs={"pk": test_item.id})
        
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == f"{test_item.name} (Copy)"
        assert response.data["description"] == test_item.description
        assert float(response.data["weight"]) == test_item.weight
        assert response.data["category"] == test_item.category.id
        
        assert Item.objects.filter(name=f"{test_item.name} (Copy)").exists()
    
    def test_search_items(self, authenticated_client, test_item):
        url = reverse("gear_items:item-search")
        
        response = authenticated_client.get(url, {"q": "Test"})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert test_item.name in [item["name"] for item in response.data]