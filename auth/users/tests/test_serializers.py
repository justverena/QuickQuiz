from django.test import TestCase
from users.serializers import UserSerializer
from users.models import Role, User

class UserSerializerTestCase(TestCase):
    def setUp(self):
        self.role_teacher, _ = Role.objects.get_or_create(name="teacher")
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            role=self.role_teacher
        )

    def test_user_serializer_fields(self):
        serializer = UserSerializer(instance=self.user)
        data = serializer.data

        expected_fields = {'id', 'username', 'email', 'role'}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_user_serializer_data_correct(self):
        serializer = UserSerializer(instance=self.user)
        data = serializer.data

        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['role'], self.user.role.name)

    def test_user_serializer_validation_error(self):
        invalid_data = {
            "username": "",
            "email": "not-an-email",
            "role": None
        }

        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)
        self.assertIn("email", serializer.errors)
