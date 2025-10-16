import jwt
from django.conf import settings
from rest_framework import authentication, exceptions


class JWTAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1].strip()
        if not token:
            raise exceptions.AuthenticationFailed("Empty token")

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token")

        user_id = payload.get("sub") or payload.get("user_id")
        role = payload.get("role")

        if not user_id:
            raise exceptions.AuthenticationFailed("Token payload missing 'sub' or 'user_id'")
        if not role:
            raise exceptions.AuthenticationFailed("Token payload missing 'role'")

        user = JWTUser(id=user_id, role=role)

        return (user, None)


class JWTUser:

    def __init__(self, id, role):
        self.id = id
        self.role = role

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"JWTUser(id={self.id}, role={self.role})"