import jwt
from rest_framework.test import APITestCase
from django.urls import reverse
from app import settings
from quizzes.models import Quiz, Question
import uuid
from rest_framework import status

class QuestionViewSetTest(APITestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()
        self.student_id = uuid.uuid4()
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
        
    def make_jwt_token(self, role, user_id):
        payload = {"sub": str(user_id), "role": role}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    def auth_headers(self, role="teacher"):
        user_id = self.teacher_id if role == "teacher" else self.student_id
        token = self.make_jwt_token(role, user_id)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    
    def test_teacher_can_create_question(self):
        response = self.client.post(self.url, self.question_data, format="json", **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "What is the boiling point of water?")

    def test_student_cannot_create_question(self):
        response = self.client.post(self.url, self.question_data, format="json", **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_get_question_list(self):
        Question.objects.create(quiz=self.quiz, text="What water", type="single")
        response = self.client.get(self.url, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    

    def test_teacher_can_update_question(self):
        q = Question.objects.create(quiz=self.quiz, text="What", type="single")
        url = reverse("question-detail", args=[q.id])
        response = self.client.patch(url, {"text": "Updated"}, format="json", **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Updated")

    def test_student_cannot_update_question(self):
        q = Question.objects.create(quiz=self.quiz, text="No", type="single")
        url = reverse("question-detail", args=[q.id])
        response = self.client.patch(url, {"title" : "Not Updated"}, format="json", **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_delete_question(self):
        q = Question.objects.create(quiz=self.quiz, text="Temp", type="single")
        url = reverse("question-detail", args=[q.id])
        response = self.client.delete(url, **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_student_cannot_delete_quiz(self):
        q = Question.objects.create(quiz=self.quiz, text="Temp", type="single")
        url = reverse("question-detail", args=[q.id])
        response = self.client.delete(url, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)