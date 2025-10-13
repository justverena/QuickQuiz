from django.urls import path
from users.views.student_views import StudentApiView

urlpatterns = [
    path("join-test/", StudentApiView.as_view(), name="student_test"),
    path("test-result/", StudentApiView.as_view(), name="student_test"),
]
