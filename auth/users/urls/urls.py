from django.urls import path, include
from ..views.base_views import (MeView, MyTokenObtainPairView, InternalValidateTokenView)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("login/", MyTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    
    path("internal/validate-token/", InternalValidateTokenView.as_view(), name="validate_token"),
    
    path("teacher/", include("users.urls.teacher_urls")),
    path("student/", include("users.urls.student_urls")),
]