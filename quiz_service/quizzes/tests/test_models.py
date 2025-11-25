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
            quiz_id=self.quiz,
            index=0,
            text="What is h2o?",
            correct_option_index=0,
            timer=30,
            type="single",
            points=2
        )
        self.assertEqual(question.quiz_id, self.quiz)
        self.assertEqual(question.type, "single")

class OptionModelTest(TestCase):
    def setUp(self):
        self.quiz = Quiz.objects.create(title="Math", teacher_id=uuid.uuid4())
        self.question = self.quiz.questions.create(
            text="2+2=?", 
            type="single",
            timer=30,
            index=0,
            correct_option_index=0)

    def test_create_option(self):
        option = Option.objects.create(question=self.question, text="4", index=0)
        is_correct = (option.index == self.question.correct_option_index)
        self.assertTrue(is_correct)

class SessionModelTest(TestCase):
    def setUp(self):
        self.quiz = Quiz.objects.create(title="Test Quiz", teacher_id=uuid.uuid4())

    def test_create_session(self):
        session = Session.objects.create(
            quiz_id=self.quiz,
            teacher_id=self.quiz.teacher_id,
            invite_code="ABC123",
            duration=10
        )
        self.assertEqual(session.quiz_id, self.quiz)
        self.assertEqual(session.status, 'waiting')