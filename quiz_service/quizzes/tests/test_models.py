from django.test import TestCase
from quizzes.models import Quiz, Question, Option, Session, Answer
import uuid
class QuizModelTest(TestCase):
    def setUp(self):
        self.teacher_id = uuid.uuid4()

    def test_cerate_quiz(self):
        quiz = Quiz.objects.create(title="History Quiz", description="Test your history knowledge", teacher_id=self.teacher_id)
        self.assertEqual(quiz.title, "History Quiz")
        self.assertEqual(quiz.description, "Test your history knowledge")
        self.assertEqual(quiz.teacher_id, self.teacher_id)
        self.assertIsInstance(quiz.id, uuid.UUID)
        self.assertIsNotNone(quiz.created_at)
        self.assertIsNotNone(quiz.updated_at)

    def test_str_representation(self):
        quiz = Quiz.objects.create(title="Math Quiz", description="Simple math", teacher_id=self.teacher_id)
        self.assertEqual(str(quiz), "Math Quiz")

    def test_blank_description(self):
        quiz = Quiz.objects.create(
        title="Empty Description Quiz",
        description="",
        teacher_id=self.teacher_id
    )
        self.assertEqual(quiz.description, "")

class QuestionModelTest(TestCase):
    def setUp(self):
        self.quiz = Quiz.objects.create(
            title="Science Quiz",
            teacher_id = uuid.uuid4()
        )
    
    def test_create_question(self):
        question = Question.objects.create(
            quiz=self.quiz,
            text="What is h2o?",
            type="single",
            points=2
        )
        self.assertEqual(question.quiz, self.quiz)
        self.assertEqual(question.type, "single")

class OptionModelTest(TestCase):
    def setUp(self):
        self.quiz = Quiz.objects.create(title="Math", teacher_id=uuid.uuid4())
        self.question = self.quiz.questions.create(text="2+2=?", type="single")

    def test_create_option(self):
        option = Option.objects.create(question=self.question, text="4", is_correct = True)
        self.assertTrue(option.is_correct)

class SessionModelTest(TestCase):
    def setUp(self):
        self.quiz = Quiz.objects.create(title="Test Quiz", teacher_id=uuid.uuid4())

    def test_create_session(self):
        session = Session.objects.create(
            quiz=self.quiz,
            invite_code="ABC123",
            duration=10
        )
        self.assertEqual(session.quiz, self.quiz)
        self.assertTrue(session.is_active)