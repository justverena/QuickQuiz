import uuid
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from users.serializers import UserSerializer
from users.models import Role, User

class UserSerializerTestCase(TestCase):
    
    def setUp(self):
        self.factory = APIRequestFactory() 
        User.objects.all().delete()
        
        self.role_admin, _ = Role.objects.get_or_create(name="admin")
        self.role_teacher, _ = Role.objects.get_or_create(name="teacher")
        self.role_student, _ = Role.objects.get_or_create(name="student")
        
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            role=self.role_teacher
        )
        
        self.admin_user = User.objects.create(
            username="admin_user",
            email="admin@example.com",
            role=self.role_admin
        )
        
    def test_user_serializer_fields(self):
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        expected_fields = {'id', 'username', 'email', 'role_name'}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_user_serializer_data_correct(self):
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        self.assertEqual(uuid.UUID(data['id']), self.user.id)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['role_name'], self.user.role.name)

    def test_user_serializer_invalid_data(self):
        invalid_data = {
            "username": "",
            "email": "not-an-email",
            "role": None
        }
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)
        self.assertIn("email", serializer.errors)

    def test_user_create_forbidden_admin_role_anonymous(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': '12345678',
            'role': 'admin'
        }
        request = self.factory.post("/users/", data)
        serializer = UserSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("role", serializer.errors)

    def test_user_create_allowed_admin_role_by_admin(self):
        data = {
            'username': 'newadmin',
            'email': 'newadmin@example.com',
            'password': '12345678',
            'role': 'admin'
        }
        request = self.factory.post("/users/", data)
        request.user = self.admin_user
        serializer = UserSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, 'newadmin')
        self.assertEqual(user.role.name, 'admin')

    def test_user_create_as_teacher_role(self):
        data = {
            'username': 'student1',
            'email': 'student1@example.com',
            'password': '12345678',
            'role': 'student'
        }
        request = self.factory.post("/users/", data)
        serializer = UserSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, 'student1')
        self.assertEqual(user.role.name, 'student')

    def test_user_update_forbidden_to_admin(self):
        data = {'role': 'admin'}
        request = self.factory.patch("/users/", data)
        request.user = self.user
        serializer = UserSerializer(instance=self.user, data=data, context={"request": request}, partial=True)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_user_update_allowed_to_admin_by_admin(self):
        data = {'role': 'admin'}
        request = self.factory.patch("/users/", data)
        request.user = self.admin_user
        serializer = UserSerializer(instance=self.user, data=data, context={"request": request}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.role.name, 'admin')
