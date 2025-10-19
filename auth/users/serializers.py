from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Role
from django.core.validators import EmailValidator
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True, required=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    username = serializers.CharField(max_length=50,
                                     validators=[UniqueValidator(queryset=User.objects.all(), message="username already exists")],
                                     required=True)
    email = serializers.EmailField(validators=[UniqueValidator(queryset=User.objects.all(), message="email already exists")],
        required=False)
    
    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role", "role_name"]
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def _request_user_is_admin(self):
        request = self.context.get("request", None)
        
        if not request:
            return False
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        try:
            return getattr(user.role, "name", None) == "admin"
        except Exception:
            return False
        
    def validate_role(self, value):
        allowed_roles = ['admin', 'teacher', 'student',]
        if value not in allowed_roles:
            raise serializers.ValidationError(
                f"unallowed role, allowed roles: {', '.join(allowed_roles)}"
            )
            
        if not Role.objects.filter(name=value).exists():
            raise serializers.ValidationError(f"Role '{value}' does not exist in DB")
        
        if value == "admin":
            if not self._request_user_is_admin():
                raise serializers.ValidationError("assigning 'admin' role via API is forbidden")
        
        return value

        
    
    def create(self, validated_data):
        role_name = validated_data.pop('role')
        
        if role_name == "admin" and not self._request_user_is_admin():
            raise serializers.ValidationError({"role": "creating user with 'admin' role is forbidden"})
        
        role_obj = Role.objects.get(name=role_name)
        password = validated_data.pop('password')
        user = User.objects.create(
            **validated_data,
            role=role_obj,
            password=make_password(password)
        )
        return user
    
    def update(self, instance, validated_data):
        role_name = validated_data.pop('role', None)
        if instance.role.name != role_name:
            if role_name:
                if role_name == "admin" and not self._request_user_is_admin():
                    raise serializers.ValidationError({"role": "assigning 'admin' role is forbidden"})
                
                if not self._request_user_is_admin():
                    raise serializers.ValidationError({"role": "only admin can change role"})
                
                try:
                    role = Role.objects.get(name=role_name)
                    instance.role = role
                except Role.DoesNotExist:
                    raise serializers.ValidationError({"role": f"Role '{role_name}' not found"})
                
        password = validated_data.pop('password', None)
        if password:
            instance.password = make_password(password)
            
        for attr, value in validated_data.items():
            if attr == 'role':
                instance.role = Role.objects.get(name=value)
            else:
                setattr(instance, attr, value)
            
        instance.save()
        return super().update(instance, validated_data)
    
    def get_role_info(self, obj):
        return {"id": obj.role.id, "name":obj.role.name}
