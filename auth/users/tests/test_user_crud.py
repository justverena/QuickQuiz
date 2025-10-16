from rest_framework.test import APITestCase
from ..models import User, Role
from rest_framework import status

class UserCRUDTests(APITestCase):
    def setUp(self):
        self.admin_role = Role.objects.get(name="admin")
        self.teacher_role = Role.objects.get(name="teacher")
        self.student_role = Role.objects.get(name="student")
        
        self.user = User.objects.create(
            username="testuser1",
            email="testuser1@example.com",
            password="123123123",
            role=self.admin_role
        )
        
        self.base_url = "/auth/users/"
        
    def test_get_all_users(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("username", response.json()[0])
        
    def test_get_user_by_id(self):
        response = self.client.get(f"{self.base_url}{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["username"], "testuser1")
        
    def test_create_user_valid(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "123123123",
            "role": "teacher"
        }
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["username"], "newuser")
    
    def test_create_user_invalid_email(self):
        data = {
            "username": "bademail",
            "email": "notemail",
            "password": "123123123",
            "role": "admin"
        }
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_create_user_invalid_role(self):
        data = {
            "username": "badrole",
            "email": "badrole@example.com",
            "password": "123123123",
            "role": "invalidrole"
        }
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_create_user_duplicate_username(self):
        data = {
            "username": "testuser1",
            "email": "asdf@example.com",
            "password": "123123123",
            "role": "teacher"
        }
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_update_user_put(self):
        data = {
            "username": "updateduser",
            "email": "updated@example.com",
            "password": "123123123",
            "role": "student"
        }
        response = self.client.put(f"{self.base_url}{self.user.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["username"], "updateduser")
    
    def test_update_user_patch(self):
        data = {"email": "patched@example.com"}
        response = self.client.patch(f"{self.base_url}{self.user.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["email"], "patched@example.com")
        
    def test_delete_user(self):
        response = self.client.delete(f"{self.base_url}{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
        
    def test_create_user_invalid_email_message(self):
        data = {
            "username": "invalidmailuser",
            "email": "not-an-email",
            "password": "123123123",
            "role": "teacher"
        }
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid email address.", response.json()["email"][0])
       
    def test_create_user_missing_fields(self):
        data = {"email": "missing@example.com"}
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.json())
        self.assertIn("password", response.json())
        self.assertIn("role", response.json())
 
    
    
    