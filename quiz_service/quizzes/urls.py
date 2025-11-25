from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuestionViewSet, OptionViewSet, SessionViewSet, StudentSessionViewSet
from .answer_views import AnswerViewSet
from django.urls import path, include

teacher_router = DefaultRouter()
teacher_router.register(r'quizzes', QuizViewSet, basename = 'quiz')
teacher_router.register(r'questions', QuestionViewSet, basename='question')
teacher_router.register(r'options', OptionViewSet, basename='option')
teacher_router.register(r'sessions', SessionViewSet, basename='session')

student_router = DefaultRouter()
student_router.register(r'sessions', StudentSessionViewSet, basename='session')
student_router.register(r'answers', AnswerViewSet, basename='answers')


urlpatterns = [
    path('api/teacher/', include(teacher_router.urls)),

    path('api/student/', include(student_router.urls)),
    
]