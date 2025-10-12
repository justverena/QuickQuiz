from rest_framework.test import APITestCase
from django.urls import reverse
from quizzes.models import Quiz
from rest_framework import status
import uuid

class QuizViewSetTest(APITestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()
        self.quiz_data = {
            "title": "Geography Quiz",
            "description": "World capitals",
            "teacher_id": str(self.teacher_id)
        }
        self.url = reverse("quiz-list")
    
    def test_create_quiz(self):
        response = self.client.post(self.url, self.quiz_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Geography Quiz")

    def test_get_quiz_list(self):
        Quiz.objects.create(**self.quiz_data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_retrieve_quiz(self):
        quiz = Quiz.objects.create(**self.quiz_data)
        url = reverse("quiz-detail", args=[quiz.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Geography Quiz")

    def test_update_quiz_before_start(self):
        quiz = Quiz.objects.create(**self.quiz_data)
        url = reverse("quiz-detail", args=[quiz.id])
        response = self.client.patch(url, {"title" : "Updated title"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated title")

    def test_delete_quiz(self):
        quiz = Quiz.objects.create(**self.quiz_data)
        url = reverse("quiz-detail", args=[quiz.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Quiz.objects.count(), 0)