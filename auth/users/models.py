import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MinLengthValidator, EmailValidator
# Create your models here.

class Role(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=30, unique=True)
    
    class Meta:
        db_table = "roles"
        
    def __str__(self):
        return self.name

class UserManager(BaseUserManager):
    def create_user(self, username, email, password, role):
        if not email:
            raise ValueError("Email required. Please enter Email.")
        if not username:
            raise ValueError("Username required. Please enter Username.")
        if not password or len(password) < 8:
            raise ValueError("Password required. Please enter password.")
        if not role:
            raise ValueError("Role required. Please enter role.")
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password, role=None):
        if role is None:
            role, _ = Role.objects.get_or_create(id=1, name="admin")
        return self.create_user(username, email, password, role)

class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="users")
    password = models.CharField(max_length=128, validators=[MinLengthValidator(8)])
    
    last_login = None
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'role']

    
    class Meta:
        db_table = "users"

    
    def __str__(self):
        return self.username
