import uuid
import jwt
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from app import settings
from quizzes.models import Quiz, Question, Option

class OptionViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher_id = uuid.uuid4()
        self.student_id = uuid.uuid4()

        # Тестовый пользователь
        self.user = get_user_model().objects.create_user(
            username="test_teacher",
            password="pass123"
        )

        # Квиз
        self.quiz = Quiz.objects.create(
            title="Math Quiz",
            description="Test",
            teacher_id=self.teacher_id
        )

        # Вопрос
        self.question = Question.objects.create(
            quiz_id=self.quiz,
            text="2 + 2 = ?",
            type="single",
            correct_option_index=0,
            timer=30,
            points=1
        )

        # Данные для создания опции
        self.option_data = {
            "question": str(self.question.id),
            "text": "4",
            "index": 0  # index нужен вместо is_correct
        }

        self.url = reverse("option-list")

    def make_jwt_token(self, role, user_id):
        payload = {"sub": str(user_id), "role": role}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    def auth_headers(self, role="teacher"):
        user_id = self.teacher_id if role == "teacher" else self.student_id
        token = self.make_jwt_token(role, user_id)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_teacher_can_create_option(self):
        response = self.client.post(
            self.url, self.option_data, format="json", **self.auth_headers("teacher")
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "4")

    def test_student_cannot_create_option(self):
        response = self.client.post(
            self.url, self.option_data, format="json", **self.auth_headers("student")
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_get_option_list(self):
        Option.objects.create(question=self.question, text="3", index=1)
        response = self.client.get(self.url, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_teacher_can_update_option(self):
        option = Option.objects.create(question=self.question, text="3", index=1)
        url = reverse("option-detail", args=[option.id])
        response = self.client.patch(
            url, {"text": "Updated"}, format="json", **self.auth_headers("teacher")
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Updated")

    def test_student_cannot_update_option(self):
        option = Option.objects.create(question=self.question, text="3", index=1)
        url = reverse("option-detail", args=[option.id])
        response = self.client.patch(
            url, {"text": "Not Updated"}, format="json", **self.auth_headers("student")
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_delete_option(self):
        option = Option.objects.create(question=self.question, text="3", index=1)
        url = reverse("option-detail", args=[option.id])
        response = self.client.delete(url, **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_student_cannot_delete_option(self):
        option = Option.objects.create(question=self.question, text="3", index=1)
        url = reverse("option-detail", args=[option.id])
        response = self.client.delete(url, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
