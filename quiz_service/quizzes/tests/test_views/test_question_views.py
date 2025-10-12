from rest_framework.test import APITestCase
from django.urls import reverse
from quizzes.models import Quiz, Question
import uuid
from rest_framework import status

class QuestionViewSetTest(APITestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()
        self.quiz = Quiz.objects.create(
            title="Science Quiz",
            description="Test your science knowledge",
            teacher_id=self.teacher_id
        )
        self.question_data = {
            "quiz": str(self.quiz.id),
            "text": "What is the boiling point of water?",
            "question_type": "text"
        }
        self.url = reverse("question-list")

    def test_create_question(self):
        response = self.client.post(self.url, self.question_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "What is the boiling point of water?")

    def test_get_question_list(self):
        Question.objects.create(quiz=self.quiz, text="What water", type="single")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    

    def test_update_question(self):
        q = Question.objects.create(quiz=self.quiz, text="What", type="single")
        url = reverse("question-detail", args=[q.id])
        response = self.client.patch(url, {"text": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Updated")

    def test_delete_question(self):
        q = Question.objects.create(quiz=self.quiz, text="Temp", type="single")
        url = reverse("question-detail", args=[q.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)