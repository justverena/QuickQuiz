from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, Role
from django.test import TestCase


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User.objects.all().delete()
        
        self.teacher_role = Role.objects.get(name="teacher")
        self.student_role = Role.objects.get(name="student")

        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="studentpass123",
            role=self.student_role,
        )
        self.teacher = User.objects.create_user(
            username="teacher1",
            email="teacher1@example.com",
            password="teacherpass123",
            role=self.teacher_role,
        )

        self.login_url = reverse("login")
        self.me_url = reverse("me")
        self.student_me_url = reverse("student_me")
        self.teacher_me_url = reverse("teacher_me")

    def test_login_returns_jwt_token(self):
        response = self.client.post(
            self.login_url,
            {"username": "student1", "password": "studentpass123"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_me_endpoint_requires_authentication(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_with_valid_token(self):
        login_response = self.client.post(
            self.login_url,
            {"username": "student1", "password": "studentpass123"},
            format="json"
        )
        access = login_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "student1")

    def test_role_restriction_student_me(self):
        login_response = self.client.post(
            self.login_url,
            {"username": "student1", "password": "studentpass123"},
            format="json"
        )
        access = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        student_response = self.client.get(self.student_me_url)
        self.assertEqual(student_response.status_code, status.HTTP_200_OK)

        teacher_response = self.client.get(self.teacher_me_url)
        self.assertEqual(teacher_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_restriction_teacher_me(self):
        login_response = self.client.post(
            self.login_url,
            {"username": "teacher1", "password": "teacherpass123"},
            format="json"
        )
        access = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        teacher_response = self.client.get(self.teacher_me_url)
        self.assertEqual(teacher_response.status_code, status.HTTP_200_OK)

        student_response = self.client.get(self.student_me_url)
        self.assertEqual(student_response.status_code, status.HTTP_403_FORBIDDEN)
