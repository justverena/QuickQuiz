import uuid
import jwt
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from app import settings
from quizzes.models import Quiz, Session, Question, Option, Answer


class StudentViewTest(APITestCase):

    def setUp(self):
        self.student_id = uuid.uuid4()
        self.teacher_id = uuid.uuid4()

        self.quiz = Quiz.objects.create(
            title="Math Quiz",
            description="Simple math questions",
            teacher_id=self.teacher_id
        )

        self.session = Session.objects.create(
            quiz=self.quiz,
            invite_code="ABC123"
        )

        self.question = Question.objects.create(
            quiz=self.quiz,
            text="2 + 2 = ?",
            type="single"
        )

        self.option = Option.objects.create(
            question=self.question,
            text="4",
            is_correct=True
        )

        self.answer_data = {
            "session": str(self.session.id),
            "question": str(self.question.id),
            "selected_options": [str(self.option.id)]
        }

    def make_jwt_token(self, role, user_id):
        payload = {"sub": str(user_id), "role": role}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    def auth_headers(self):
        token = self.make_jwt_token("student", self.student_id)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_student_can_create_answer(self):
        url = reverse("answers-list")
        response = self.client.post(url, self.answer_data, format="json", **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["student_id"], str(self.student_id))

    def test_student_can_get_answers_list(self):
        Answer.objects.create(
            session=self.session,
            student_id=self.student_id,
            question=self.question,
            selected_options=[self.option.id]
        )
        url = reverse("answers-list")
        response = self.client.get(url, **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_student_can_retrieve_answer(self):
        answer = Answer.objects.create(
            session=self.session,
            student_id=self.student_id,
            question=self.question,
            selected_options=[self.option.id]
        )
        url = reverse("answers-detail", args=[answer.id])
        response = self.client.get(url, **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(answer.id))

    def test_student_cannot_update_answer(self):
        answer = Answer.objects.create(
            session=self.session,
            student_id=self.student_id,
            question=self.question,
            selected_options=[self.option.id]
        )
        url = reverse("answers-detail", args=[answer.id])
        response = self.client.patch(url, {"selected_options": []}, format="json", **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_delete_answer(self):
        answer = Answer.objects.create(
            session=self.session,
            student_id=self.student_id,
            question=self.question,
            selected_options=[self.option.id]
        )
        url = reverse("answers-detail", args=[answer.id])
        response = self.client.delete(url, **self.auth_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)