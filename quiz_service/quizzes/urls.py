from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuestionViewSet, OptionViewSet, SessionViewSet
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

teacher_router = DefaultRouter()
teacher_router.register(r'quizzes', QuizViewSet, basename = 'quiz')
teacher_router.register(r'questions', QuestionViewSet, basename='question')
teacher_router.register(r'options', OptionViewSet, basename='option')
teacher_router.register(r'sessions', SessionViewSet, basename='session')

student_router = DefaultRouter()
student_router.register(r'sessions', SessionViewSet, basename='session')

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    path('api/teacher/', include(teacher_router.urls)),

    path('api/student/', include(student_router.urls)),

]