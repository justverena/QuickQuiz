from django.test import TestCase
from quizzes.models import Quiz, Question, Option, Session, Answer
import uuid
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from quizzes.models import Quiz, Session, Question, Option, Answer
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


class ModelsSmokeTests(TestCase):
    def test_create_quiz_session_question_option(self):
        quiz = Quiz.objects.create(
            title="Sample Quiz",
            teacher_id=uuid.uuid4()
        )
        session = Session.objects.create(
            quiz=quiz, invite_code="ABC123", is_active=True
        )
        q1 = Question.objects.create(quiz=quiz, text="2+2=?")
        Option.objects.create(question=q1, text="3", is_correct=False)
        o2 = Option.objects.create(question=q1, text="4", is_correct=True)

        self.assertTrue(quiz.id)
        self.assertEqual(session.invite_code, "ABC123")
        self.assertEqual(q1.quiz, quiz)
        self.assertTrue(o2.is_correct)

    def test_answer_model_basic(self):
        quiz = Quiz.objects.create(
            title="Math",
            teacher_id=uuid.uuid4()
        )
        session = Session.objects.create(
            quiz=quiz, invite_code="MATH1", is_active=True
        )
        q = Question.objects.create(quiz=quiz, text="1+1=?")
        o = Option.objects.create(question=q, text="2", is_correct=True)

        ans = Answer.objects.create(
            session=session,
            student_id=str(uuid.uuid4()),
            question=q,
            selected_options=[str(o.id)],
            is_correct=True,
        )
        self.assertTrue(ans.id)
        self.assertTrue(ans.is_correct)