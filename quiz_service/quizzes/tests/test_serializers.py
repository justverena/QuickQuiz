from django.test import TestCase
from quizzes.models import Quiz
from quizzes.serializers import QuizSerializer, QuestionSerializer
import uuid
from django.test import TestCase
from quizzes.models import Quiz, Session, Question, Option
from quizzes.serializers import SessionSerializer, QuestionSerializer

class QuizSerializerTest(TestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()
        self.quiz_data = {
            "title":"Math Quiz",
            "description":"Algebra quiz",
            "teacher_id": str(self.teacher_id)
        }

    def test_valid_data_serialization(self):
        serializer = QuizSerializer(data=self.quiz_data)
        self.assertTrue(serializer.is_valid())
        quiz = serializer.save()
        self.assertEqual(quiz.title, "Math Quiz")
    
    def test_missing_title(self):
        invalid_data = self.quiz_data.copy()
        invalid_data.pop("title")
        serializer = QuizSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)

class QuestionSerializerTest(TestCase):
    def setUp(self):
        self.quiz = Quiz.objects.create(
            title="Science Quiz",
            description="Science",
            teacher_id=uuid.uuid4()
        )
        self.question_data = {
            "quiz": str(self.quiz.id),
            "text": "What is the boiling point of water?",
            "question_type": "text"
        }

    def test_valid_question(self):
        serializer = QuestionSerializer(data=self.question_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()


class SerializersTests(TestCase):
    def test_session_serializer_fields(self):
        quiz = Quiz.objects.create(title="History", teacher_id=uuid.uuid4())
        session = Session.objects.create(
            quiz=quiz,
            invite_code="HIS123",
            is_active=True,
        )
        data = SessionSerializer(session).data
        self.assertIn("id", data)
        self.assertEqual(data.get("invite_code"), "HIS123")
        self.assertTrue(data.get("is_active"))

    def test_question_serializer_includes_options(self):
        quiz = Quiz.objects.create(title="Math", teacher_id=uuid.uuid4())
        q = Question.objects.create(quiz=quiz, text="3+5=?")
        Option.objects.create(question=q, text="8", is_correct=True)
        Option.objects.create(question=q, text="7", is_correct=False)

        data = QuestionSerializer(q).data
        self.assertEqual(data["text"], "3+5=?")
        self.assertIn("options", data)
        self.assertTrue(any(opt["text"] == "8" for opt in data["options"]))