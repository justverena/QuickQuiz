from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuestionViewSet, OptionViewSet, SessionViewSet, AnswerViewSet, JoinSessionView, SessionQuestionsView, SubmitAnswersView, SessionResultsView
from django.urls import path, include

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename = 'quiz')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'options', OptionViewSet, basename='option')
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'student/answers', AnswerViewSet, basename='student-answers')

urlpatterns = [
    path('', include(router.urls)),
]



urlpatterns += [
    path("student/sessions/join/", JoinSessionView.as_view(), name="student-join"),
    path("student/sessions/<uuid:session_id>/questions/", SessionQuestionsView.as_view(), name="student-questions"),
    path("student/sessions/<uuid:session_id>/answers/", SubmitAnswersView.as_view(), name="student-answers"),
    path("student/sessions/<uuid:session_id>/results/", SessionResultsView.as_view(), name="student-results"),
]