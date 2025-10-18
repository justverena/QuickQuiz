import jwt
from rest_framework.test import APITestCase
from rest_framework import status
from app import settings
from quizzes.models import Quiz, Session
from django.urls import reverse
from datetime import datetime, timedelta
import uuid


class SessionViewSetTest(APITestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()
        self.student_id = uuid.uuid4()
        self.quiz = Quiz.objects.create(
            title="Science Quiz",
            description="Session test",
            teacher_id=self.teacher_id
        )
        self.session_data = {
            "quiz": self.quiz.id,
            "invite_code": "ABC123",
            "duration": 10,
        }
        self.url = reverse("session-list")
        
    def make_jwt_token(self, role, user_id):
        payload = {"sub": str(user_id), "role": role}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    def auth_headers(self, role="teacher"):
        user_id = self.teacher_id if role == "teacher" else self.student_id
        token = self.make_jwt_token(role, user_id)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    
    def test_teacher_can_create_session(self):
        response = self.client.post(self.url, self.session_data, format="json", **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Session.objects.count(), 1)

    def test_student_cannot_create_session(self):
        response = self.client.post(self.url, self.session_data, format="json", **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_update_session(self):
        session = Session.objects.create(quiz=self.quiz, invite_code="OLD123", duration=10)
        url = reverse("session-detail", args=[session.id])
        response = self.client.put(url, {
            "quiz": self.quiz.id,
            "invite_code": "NEW123",
            "duration": 20
        }, format="json", **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.invite_code, "NEW123")
        self.assertEqual(session.duration, 20)

    def test_student_cannot_update_session(self):
        session = Session.objects.create(quiz=self.quiz, invite_code="OLD123", duration=10)
        url = reverse("session-detail", args=[session.id])
        response = self.client.put(url, {
            "quiz": self.quiz.id,
            "invite_code": "NEW123",
            "duration": 20
        }, format="json", **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_delete_session(self):
        session = Session.objects.create(quiz=self.quiz, invite_code="DEL123", duration=10)
        url = reverse("session-detail", args=[session.id])
        response = self.client.delete(url, **self.auth_headers("teacher"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Session.objects.count(), 0)

    def test_student_cannot_delete_session(self):
        session = Session.objects.create(quiz=self.quiz, invite_code="DEL123", duration=10)
        url = reverse("session-detail", args=[session.id])
        response = self.client.delete(url, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_student_get_session_by_invite_code(self):
        session = Session.objects.create(
            quiz=self.quiz,
            invite_code="INV123",
            duration=20
    )
        url = reverse("session-get-by-invite")
        response = self.client.get(url, {"invite_code": "INV123"}, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["invite_code"], "INV123")
        self.assertEqual(response.data["duration"], 20)
        self.assertEqual(str(response.data["quiz"]), str(self.quiz.id))

    def test_student_get_session_with_wrong_invite_code(self):
        url = reverse("session-get-by-invite")
        response = self.client.get(url, {"invite_code": "WRONGCODE"}, **self.auth_headers("student"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)