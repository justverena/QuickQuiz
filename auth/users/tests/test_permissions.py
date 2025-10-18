from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import Role
from users.permissions import IsOwner

User = get_user_model()

class IsOwnerPermissionTests(TestCase):
    def setUp(self):
        self.role_admin = Role.objects.get(name='admin')
        self.role_teacher = Role.objects.get(name='teacher')
        self.role_student = Role.objects.get(name='student')

        self.admin = User.objects.create(
            username='admin_user',
            email='admin3@example.com',
            role=self.role_admin
        )
        self.teacher = User.objects.create(
            username='teacher_user',
            email='teacher3@example.com',
            role=self.role_teacher
        )
        self.student = User.objects.create(
            username='student_user',
            email='student3@example.com',
            role=self.role_student
        )

        self.permission = IsOwner()

    def test_admin_has_permission_for_any_user(self):
        request = type('Request', (), {'user': self.admin})()
        self.assertTrue(self.permission.has_permission(request, None))
        self.assertTrue(self.permission.has_object_permission(request, None, self.teacher))
        self.assertTrue(self.permission.has_object_permission(request, None, self.student))

    def test_owner_has_permission_for_self(self):
        request = type('Request', (), {'user': self.teacher})()
        self.assertTrue(self.permission.has_permission(request, None))
        self.assertTrue(self.permission.has_object_permission(request, None, self.teacher))

    def test_owner_denied_for_other_user(self):
        request = type('Request', (), {'user': self.teacher})()
        self.assertTrue(self.permission.has_permission(request, None))
        self.assertFalse(self.permission.has_object_permission(request, None, self.student))

    def test_anonymous_user_denied(self):
        request = type('Request', (), {'user': type('Anon', (), {'is_authenticated': False})()})()
        self.assertFalse(self.permission.has_permission(request, None))
