import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class TestUserModel(TestCase):

    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "weight_unit": "g",
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_create_user(self):
        self.assertEqual(self.user.username, self.user_data["username"])
        self.assertEqual(self.user.email, self.user_data["email"])
        self.assertEqual(self.user.weight_unit, self.user_data["weight_unit"])
        self.assertTrue(self.user.check_password(self.user_data["password"]))
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpassword123",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_string_representation(self):
        self.assertEqual(str(self.user), self.user_data["username"])

    def test_user_email_unique(self):
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="anotheruser",
                email=self.user_data["email"],
                password="password123",
            )