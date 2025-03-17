import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

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
def test_user_token(test_user):
    token, _ = Token.objects.get_or_create(user=test_user)
    return token


@pytest.fixture
def authenticated_client(api_client, test_user_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {test_user_token.key}")
    return api_client


@pytest.mark.django_db
class TestUserAPI:    
    def test_register_user(self, api_client):
        url = reverse("users:register")
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword123",
            "password_confirm": "newpassword123",
            "weight_unit": "g"
        }
        
        response = api_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "token" in response.data
        assert response.data["user"]["username"] == data["username"]
        assert response.data["user"]["email"] == data["email"]
        assert response.data["user"]["weight_unit"] == data["weight_unit"]
        
        assert User.objects.filter(username=data["username"]).exists()
    
    def test_register_user_password_mismatch(self, api_client):
        url = reverse("users:register")
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword123",
            "password_confirm": "differentpassword",
            "weight_unit": "g"
        }
        
        response = api_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data
    
    def test_login_user(self, api_client, test_user):
        url = reverse("users:login")
        data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        
        response = api_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.data
        assert response.data["user"]["username"] == test_user.username
        assert response.data["user"]["email"] == test_user.email
    
    def test_login_invalid_credentials(self, api_client, test_user):
        url = reverse("users:login")
        data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = api_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data
    
    def test_logout(self, authenticated_client):
        url = reverse("users:logout")
        
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        response = authenticated_client.get(reverse("users:user-me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_me(self, authenticated_client, test_user):
        url = reverse("users:user-me")
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == test_user.username
        assert response.data["email"] == test_user.email
    
    def test_update_user(self, authenticated_client, test_user):
        url = reverse("users:user-detail", kwargs={"pk": test_user.id})
        data = {
            "username": test_user.username,
            "first_name": "New",
            "last_name": "Name",
            "bio": "Updated bio",
            "weight_unit": "oz"
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == data["first_name"]
        assert response.data["last_name"] == data["last_name"]
        assert response.data["bio"] == data["bio"]
        assert response.data["weight_unit"] == data["weight_unit"]
        
        test_user.refresh_from_db()
        assert test_user.first_name == data["first_name"]
        assert test_user.last_name == data["last_name"]
        assert test_user.bio == data["bio"]
        assert test_user.weight_unit == data["weight_unit"]
    
    def test_change_password(self, authenticated_client, test_user):
        url = reverse("users:user-change-password")
        data = {
            "old_password": "testpassword123",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.data
        assert "detail" in response.data
        
        test_user.refresh_from_db()
        assert test_user.check_password(data["new_password"])
        
        old_token = f"Token {test_user_token.key}"
        authenticated_client.credentials(HTTP_AUTHORIZATION=old_token)
        response = authenticated_client.get(reverse("users:user-me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED