from django.test import TestCase
from users.models import Role, User

class UserAndRoleModelTests(TestCase):

    
    def test_user_str(self):
        role = Role.objects.get(name="student")
        user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strongpass",
            role=role
            
        )
        
        self.assertEqual(str(user), "alice")
