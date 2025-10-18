from rest_framework.test import APITestCase
from users.models import User, Role
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class UserCRUDTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_role, _ = Role.objects.get_or_create(name="admin")
        cls.teacher_role, _ = Role.objects.get_or_create(name="teacher")
        cls.student_role, _ = Role.objects.get_or_create(name="student")

        cls.admin_user = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="123123123",
            role=cls.admin_role
        )
        cls.teacher_user = User.objects.create_user(
            username="teacher1",
            email="teacher1@example.com",
            password="123123123",
            role=cls.teacher_role
        )

        cls.admin_token = str(RefreshToken.for_user(cls.admin_user).access_token)
        cls.teacher_token = str(RefreshToken.for_user(cls.teacher_user).access_token)

        cls.base_url = "/auth/users/"
        cls.register_url = "/auth/register/"
        cls.me_url = "/auth/me/"

    def test_register_user_valid(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "123123123",
            "role": "teacher"
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["username"], "newuser")


    def test_register_user_forbidden_admin_role(self):
        data = {
            "username": "fakeadmin",
            "email": "fakeadmin@example.com",
            "password": "123123123",
            "role": "admin"
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.json())

    def test_me_authenticated_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["username"], "teacher1")

    def test_me_unauthenticated(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_by_id_as_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}")
        response = self.client.get(f"{self.base_url}{self.teacher_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["username"], "teacher1")

    def test_get_user_by_id_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}")
        response = self.client.get(f"{self.base_url}{self.admin_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_user_as_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}")
        data = {"email": "patched@example.com"}
        response = self.client.patch(f"{self.base_url}{self.teacher_user.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["email"], "patched@example.com")

    def test_patch_user_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}")
        data = {"email": "forbidden@example.com"}
        response = self.client.patch(f"{self.base_url}{self.admin_user.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_as_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}")
        response = self.client.delete(f"{self.base_url}{self.teacher_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.teacher_user.id).exists())

    def test_delete_user_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}")
        response = self.client.delete(f"{self.base_url}{self.admin_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_forbidden_to_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}")
        data = {"role": "admin"}
        response = self.client.patch(f"{self.base_url}{self.teacher_user.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.json())
