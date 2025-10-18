from django.urls import path, include
from ..views.base_views import (MeView, MyTokenObtainPairView,UserViewSet, RegisterView)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", MyTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    
    # path("internal/validate-token/", InternalValidateTokenView.as_view(), name="validate_token"),
    
    path("", include(router.urls)),
]