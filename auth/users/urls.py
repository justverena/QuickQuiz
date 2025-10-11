from django.urls import path
from .views import MeView, MyTokenObtainPairView, StudentMeView, TeacherMeView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("login/", MyTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    
    path("student/me/", StudentMeView.as_view(), name="student_me"),
    path("teacher/me/", TeacherMeView.as_view(), name="teacher_me")
]