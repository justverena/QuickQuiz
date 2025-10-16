import jwt
from rest_framework.test import APITestCase
from django.urls import reverse
from app import settings
from quizzes.models import Quiz
from rest_framework import status
import uuid

class QuizViewSetTest(APITestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()
        self.student_id = uuid.uuid4()
        self.quiz_data = {
            "title": "Geography Quiz",
            "description": "World capitals",
            "teacher_id": str(self.teacher_id)
        }
        self.url = reverse("quiz-list")


    def make_jwt_token(self, role, user_id):
        payload = {"sub": str(user_id), "role": role}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    def auth_headers(self, role="teacher"):
        user_id = self.teacher_id if role == "teacher" else self.student_id
        token = self.make_jwt_token(role, user_id)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_teacher_can_create_quiz(self):
        response = self.client.post(self.url, self.quiz_data, format="json", **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Geography Quiz")

    def test_student_cannot_create_quiz(self):
        response = self.client.post(self.url, self.quiz_data, format="json", **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_get_quiz_list(self):
        Quiz.objects.create(**self.quiz_data)
        response = self.client.get(self.url, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_student_retrieve_quiz(self):
        quiz = Quiz.objects.create(**self.quiz_data)
        url = reverse("quiz-detail", args=[quiz.id])
        response = self.client.get(url, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Geography Quiz")

    def test_teacher_can_update_quiz_before_start(self):
        quiz = Quiz.objects.create(**self.quiz_data)
        url = reverse("quiz-detail", args=[quiz.id])
        response = self.client.patch(url, {"title" : "Updated title"}, format="json", **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated title")

    def test_student_cannot_update_quiz(self):
        quiz = Quiz.objects.create(**self.quiz_data)
        url = reverse("quiz-detail", args=[quiz.id])
        response = self.client.patch(url, {"title" : "Not Updated title"}, format="json", **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_delete_quiz(self):
        quiz = Quiz.objects.create(**self.quiz_data)
        url = reverse("quiz-detail", args=[quiz.id])
        response = self.client.delete(url, **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Quiz.objects.count(), 0)
    
    def test_student_cannot_delete_quiz(self):
        quiz = Quiz.objects.create(**self.quiz_data)
        url = reverse("quiz-detail", args=[quiz.id])
        response = self.client.delete(url, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)