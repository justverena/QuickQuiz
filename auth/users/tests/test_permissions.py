from django.test import TestCase
from django.contrib.auth import get_user_model
from users.permissions import IsTeacher, IsStudent
from users.models import Role

User = get_user_model()


class PermissionTests(TestCase):
    def setUp(self):
        self.role_teacher = Role.objects.get(name='teacher')
        self.role_student = Role.objects.get(name='student')
        self.role_admin = Role.objects.get(name='admin')
        
        self.teacher = User.objects.create(
            username='teacher_user',
            email='teacher2@example.com',
            role=self.role_teacher
        )
        self.student = User.objects.create(
            username='student_user',
            email='student2@example.com',
            role=self.role_student
        )
        self.admin = User.objects.create(
            username='admin_user',
            email='admin2@example.com',
            role=self.role_admin
        )

        self.is_teacher = IsTeacher()
        self.is_student = IsStudent()

    def test_is_teacher_permission(self):
        request = type('Request', (), {'user': self.teacher})()
        self.assertTrue(self.is_teacher.has_permission(request, None))

        request = type('Request', (), {'user': self.student})()
        self.assertFalse(self.is_teacher.has_permission(request, None))

        request = type('Request', (), {'user': self.admin})()
        self.assertFalse(self.is_teacher.has_permission(request, None))

    def test_is_student_permission(self):
        request = type('Request', (), {'user': self.student})()
        self.assertTrue(self.is_student.has_permission(request, None))

        request = type('Request', (), {'user': self.teacher})()
        self.assertFalse(self.is_student.has_permission(request, None))

        request = type('Request', (), {'user': self.admin})()
        self.assertFalse(self.is_student.has_permission(request, None))
