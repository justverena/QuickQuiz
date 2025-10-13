from django.urls import path
from users.views.teacher_views import TeacherApiView

urlpatterns = [
    path("add-test/", TeacherApiView.as_view(), name="teacher_test"),
]
