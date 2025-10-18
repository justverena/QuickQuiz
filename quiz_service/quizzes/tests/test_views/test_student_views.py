from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
import uuid

from quizzes.models import Quiz, Session, Question, Option, Answer

User = get_user_model()


class StudentViewsTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="stud", email="stud@example.com", password="pass12345"
        )
        self.client.force_authenticate(
            user=self.student,
            token={"role": "student", "user_id": str(self.student.id)},
        )
        self.quiz = Quiz.objects.create(
            title="QuickQuiz Demo",
            description="Student views tests",
            teacher_id=uuid.uuid4(),
        )
        self.active_session = Session.objects.create(
            quiz=self.quiz,
            invite_code="ABC123",
            is_active=True,
            duration=10,
        )
        self.inactive_session = Session.objects.create(
            quiz=self.quiz,
            invite_code="OLD999",
            is_active=False,
            duration=10,
        )

        self.q1 = Question.objects.create(quiz=self.quiz, text="2+2=?")
        self.q2 = Question.objects.create(quiz=self.quiz, text="3+1=?")

        self.q1_correct = Option.objects.create(question=self.q1, text="4", is_correct=True)
        self.q1_wrong   = Option.objects.create(question=self.q1, text="5", is_correct=False)
        self.q2_correct = Option.objects.create(question=self.q2, text="4", is_correct=True)
        self.q2_wrong   = Option.objects.create(question=self.q2, text="3", is_correct=False)

    def test_join_session_success(self):
        url = reverse("student-join")
        resp = self.client.post(url, {"invite_code": "ABC123"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("id", resp.data)
        self.assertEqual(resp.data.get("invite_code"), "ABC123")
      
    def test_join_session_not_found(self):
        url = reverse("student-join")
        resp = self.client.post(url, {"invite_code": "NOPE"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_session_questions_returns_questions(self):
        url = reverse("student-questions", kwargs={"session_id": self.active_session.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        texts = [q["text"] for q in resp.data]
        self.assertIn("2+2=?", texts)
        self.assertIn("3+1=?", texts)

    def test_submit_answers_success_and_persists_is_correct(self):
        url = reverse("student-answers", kwargs={"session_id": self.active_session.id})
        payload = {
            "answers": [
                {
                    "question_id": str(self.q1.id),
                    "selected_options": [str(self.q1_correct.id)],  # <-- вот здесь было opt1_correct
                },
                {
                    "question_id": str(self.q2.id),
                    "selected_options": [str(self.q2_wrong.id)],
                },
            ]
        }
        
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("created_answers", resp.data)
        self.assertEqual(len(resp.data["created_answers"]), 2)
        
        answers = Answer.objects.filter(
            session=self.active_session,
            student_id=str(self.student.id)
            ).order_by("question_id")
        self.assertEqual(answers.count(), 2)
        self.assertTrue(any(a.is_correct for a in answers))
        self.assertTrue(any(not a.is_correct for a in answers))

    def test_submit_answers_inactive_session_returns_400(self):
        url = reverse("student-answers", kwargs={"session_id": self.inactive_session.id})
        payload = {
            "answers": [
                {"question_id": str(self.q1.id), "selected_options": [str(self.q1_correct.id)]}
            ]
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(str(resp.data["detail"]).lower().startswith("session is not active"))

    def test_session_results_only_after_session_end(self):
        submit_url = reverse("student-answers", kwargs={"session_id": self.active_session.id})
        payload = {
            "answers": [
                {
                    "question_id": str(self.q1.id),
                    "selected_options": [str(self.q1_correct.id)],  
                }
            ]
        }

        r_submit = self.client.post(submit_url, payload, format="json")
        self.assertEqual(r_submit.status_code, status.HTTP_201_CREATED)

        results_url = reverse("student-results", kwargs={"session_id": self.active_session.id})
        r1 = self.client.get(results_url)
        self.assertEqual(r1.status_code, status.HTTP_400_BAD_REQUEST)

        self.active_session.is_active = False
        self.active_session.ended_at = timezone.now()
        self.active_session.save()

        r2 = self.client.get(results_url)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data["quiz_title"], self.active_session.quiz.title)
        self.assertEqual(r2.data["total_questions"], 2)
        self.assertEqual(r2.data["correct_answers"], 1)
        self.assertEqual(r2.data["score_percent"], 50.0)

    def test_requires_student_role(self):
        self.client.force_authenticate(
            user=self.student,
            token={"role": "teacher", "user_id": str(self.student.id)},
        )
        url = reverse("student-join")
        resp = self.client.post(url, {"invite_code": "ABC123"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only students", str(resp.data))  