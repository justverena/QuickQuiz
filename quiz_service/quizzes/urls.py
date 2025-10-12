from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuestionViewSet, OptionViewSet, SessionViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename = 'quiz')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'options', OptionViewSet, basename='option')
router.register(r'sessions', SessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
]