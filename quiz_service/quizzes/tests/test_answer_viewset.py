import jwt
import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from app import settings
from quizzes.models import Answer, Quiz, Session, Question, Option

class AnswerViewSetTest(APITestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()
        self.student_id = uuid.uuid4()

        self.quiz = Quiz.objects.create(
            title="GQ",
            description="desc",
            teacher_id=str(self.teacher_id)
        )
        self.session = Session.objects.create(quiz=self.quiz, is_active=True)
        self.question = Question.objects.create(
            quiz=self.quiz, text="Q1", type="single", points=1
        )
        self.opt1 = Option.objects.create(question=self.question, text="A", is_correct=True)
        self.opt2 = Option.objects.create(question=self.question, text="B", is_correct=False)

        self.url_list = reverse("answer-list")

    def make_jwt_token(self, role, user_id):
        payload = {"sub": str(user_id), "role": role}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    def auth_headers(self, role="teacher"):
        user_id = self.teacher_id if role == "teacher" else self.student_id
        token = self.make_jwt_token(role, user_id)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_student_can_create_answer(self):
        data = {
            "session": str(self.session.id),
            "question": str(self.question.id),
            "selected_options": [str(self.opt1.id)],
        }
        r = self.client.post(self.url_list, data, format="json", **self.auth_headers("student"))
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_teacher_cannot_create_answer(self):
        data = {
            "session": str(self.session.id),
            "question": str(self.question.id),
            "selected_options": [str(self.opt1.id)],
        }
        r = self.client.post(self.url_list, data, format="json", **self.auth_headers("teacher"))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_lists_only_their_answers(self):
        Answer.objects.create(
            session=self.session, question=self.question,
            student_id=str(self.student_id),
            selected_options=[str(self.opt1.id)], is_correct=True
        )
        Answer.objects.create(
            session=self.session, question=self.question,
            student_id=str(uuid.uuid4()),
            selected_options=[str(self.opt2.id)], is_correct=False
        )
        r = self.client.get(self.url_list, **self.auth_headers("student"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)

    def test_teacher_lists_all_answers(self):
        Answer.objects.create(
            session=self.session, question=self.question,
            student_id=str(self.student_id),
            selected_options=[str(self.opt1.id)], is_correct=True
        )
        Answer.objects.create(
            session=self.session, question=self.question,
            student_id=str(uuid.uuid4()),
            selected_options=[str(self.opt2.id)], is_correct=False
        )
        r = self.client.get(self.url_list, **self.auth_headers("teacher"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(r.data), 2)
