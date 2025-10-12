import uuid
from rest_framework.test import APITestCase
from rest_framework import status
from quizzes.models import Quiz, Question, Option
from django.urls import reverse


class OptionViewSetTest(APITestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()
        self.quiz = Quiz.objects.create(
            title="Math Quiz",
            description="Test",
            teacher_id=self.teacher_id
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            text="2 + 2 = ?",
            type="single",
            points=1
        )
        self.option_data = {
            "question": self.question.id,
            "text": "4",
            "is_correct": True
        }
        self.url = reverse("option-list")
    
    def test_create_option(self):
        response = self.client.post(self.url, self.option_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "4")

    def test_get_option_list(self):
        Option.objects.create(question=self.question, text="3", is_correct=False)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    

    def test_update_option(self):
        option = Option.objects.create(question=self.question, text="3", is_correct=False)
        url = reverse("option-detail", args=[option.id])
        response = self.client.patch(url, {"text": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Updated")

    def test_delete_option(self):
        option = Option.objects.create(question=self.question, text="3", is_correct=False)
        url = reverse("option-detail", args=[option.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)