from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

'''
class IsStudent(BasePermission):
    def has_permission(self, request, view):
        role = getattr(request.user, "role", None) or getattr(request.auth, "get", lambda key: None)("role")
        if not role and isinstance(request.auth, dict):
            role = request.auth.get("role")
        if role != "student":
            raise PermissionDenied("Only students can perform this action.")
        return True
'''
class IsStudent(BasePermission):
    def has_permission(self, request, view):
        role = None
        if isinstance(getattr(request, "auth", None), dict):
            role = request.auth.get("role")
        if role is None and hasattr(request.user, "role"):
            role = getattr(request.user, "role", None)
        return role == "student"