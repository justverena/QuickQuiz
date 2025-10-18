from rest_framework import viewsets, permissions
from .models import Quiz, Question, Option, Session, Answer
from .serializers import QuizSerializer, QuestionSerializer, OptionSerializer, SessionSerializer, AnswerSerializer


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all().order_by('-created_at')
    serializer_class = QuizSerializer

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer


from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from quizzes.models import Session, Question, Answer
from quizzes.serializers import SessionSerializer, QuestionSerializer
from quizzes.permissions import IsStudent
from rest_framework.exceptions import PermissionDenied


class JoinSessionView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        invite_code = request.data.get("invite_code")
        student_id = request.auth.get("user_id")

        session = Session.objects.filter(invite_code=invite_code, is_active=True).first()
        if not session:
            return Response({"detail": "Session not found or inactive."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SessionQuestionsView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        session_id = self.kwargs["session_id"]
        return Question.objects.filter(quiz__sessions__id=session_id)


class SubmitAnswersView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, session_id):
        student_id = request.auth.get("user_id")
        data = request.data.get("answers", [])

        session = get_object_or_404(Session, id=session_id)
        if not session.is_active:
            return Response(
                {"detail": "Session is not active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_ids = []
        for item in data:
            question_id = item.get("question_id")
            selected_options = item.get("selected_options", [])

            question = get_object_or_404(
                Question.objects.filter(quiz=session.quiz),
                id=question_id
            )

            '''ser = AnswerSerializer(data={
                "session": str(session.id),
                "student_id": str(student_id),
                "question": str(question.id),
                "selected_options": selected_options, 
            }) '''
            ser = AnswerSerializer(data={
                "session": str(session.id),
                "student_id": str(student_id),
                "question": str(question.id),
                "selected_options": [str(x) for x in selected_options],
            })

            ser.is_valid(raise_exception=True)
            ans = ser.save()
            created_ids.append(str(ans.id))

        return Response({"created_answers": created_ids}, status=status.HTTP_201_CREATED)


class SessionResultsView(APIView):
   
    permission_classes = [IsStudent]

    def get(self, request, session_id):
        student_id = request.auth.get("user_id")
        session = get_object_or_404(Session, id=session_id)
        if session.is_active:
            return Response({"detail": "Session is still active."}, status=status.HTTP_400_BAD_REQUEST)

        answers = Answer.objects.filter(session=session, student_id=student_id)
        total_questions = session.quiz.questions.count()
        correct_answers = answers.filter(is_correct=True).count()
        score = (correct_answers / total_questions * 100) if total_questions else 0

        return Response({
            "quiz_title": session.quiz.title,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "score_percent": round(score, 2),
        })

class AnswerViewSet(viewsets.ModelViewSet):

    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_queryset(self):
        user_id = None
        if getattr(self.request, "auth", None):
            user_id = self.request.auth.get("user_id")
        return Answer.objects.filter(student_id=str(user_id))

    def perform_create(self, serializer):
        user_id = self.request.auth.get("user_id")
        serializer.save(student_id=user_id)

    def perform_update(self, serializer):
        instance = self.get_object()
        user_id = self.request.auth.get("user_id")
        if str(instance.student_id) != str(user_id):
            raise PermissionDenied("You can only modify your own answers.")
        serializer.save()

    def perform_destroy(self, instance):
        user_id = self.request.auth.get("user_id")
        if str(instance.student_id) != str(user_id):
            raise PermissionDenied("You can only delete your own answers.")
        instance.delete()