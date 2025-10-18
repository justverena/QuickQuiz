from rest_framework import permissions

# class IsTeacher(permissions.BasePermission):
#     def has_permission(self, request, view):
#         return (
#             request.user
#             and request.user.is_authenticated
#             and getattr(request.user.role, "name", None) == "teacher"
#         )


# class IsStudent(permissions.BasePermission):
#     def has_permission(self, request, view):
#         return (
#             request.user
#             and request.user.is_authenticated
#             and getattr(request.user.role, "name", None) == "student"
#         )

class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        try:
            is_admin = getattr(request.user, "role", None) and request.user.role.name == "admin"
        except Exception:
            is_admin = False

        if is_admin:
            return True

        return getattr(obj, "id", None) == getattr(request.user, "id", None)