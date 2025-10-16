from django.urls import path, include
from ..views.base_views import (MeView, MyTokenObtainPairView, InternalValidateTokenView, UserViewSet)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path("login/", MyTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    
    path("internal/validate-token/", InternalValidateTokenView.as_view(), name="validate_token"),
    
    path("teacher/", include("users.urls.teacher_urls")),
    path("student/", include("users.urls.student_urls")),
    
    path("", include(router.urls)),
]