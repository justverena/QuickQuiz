from rest_framework.test import APITestCase
from rest_framework import status
from quizzes.models import Quiz, Session
from django.urls import reverse
from datetime import datetime, timedelta
import uuid


class SessionViewSetTest(APITestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()
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
        self.list_url = reverse("session-list")

    def test_create_session(self):
        response = self.client.post(self.list_url, self.session_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Session.objects.count(), 1)

    def test_list_sessions(self):
        Session.objects.create(quiz=self.quiz, invite_code="CODE123", duration=15)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_session(self):
        session = Session.objects.create(quiz=self.quiz, invite_code="OLD123", duration=10)
        url = reverse("session-detail", args=[session.id])
        response = self.client.put(url, {
            "quiz": self.quiz.id,
            "invite_code": "NEW123",
            "duration": 20
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.invite_code, "NEW123")
        self.assertEqual(session.duration, 20)

    def test_delete_session(self):
        session = Session.objects.create(quiz=self.quiz, invite_code="DEL123", duration=10)
        url = reverse("session-detail", args=[session.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Session.objects.count(), 0)