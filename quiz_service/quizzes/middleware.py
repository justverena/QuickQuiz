import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from django.conf import settings
from urllib.parse import parse_qs


class SimpleUser:
    def __init__(self, user_id, role, username=""):
        self.id = str(user_id)
        self.role = role
        self.username = username or ""


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        instance = JWTAuthMiddlewareInstance(scope, self.inner)
        return await instance(receive, send)


class JWTAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = dict(scope)
        self.inner = inner

    async def __call__(self, receive, send):
        self.scope["user"] = None

        # query string
        qs = self.scope.get("query_string", b"").decode()
        try:
            params = parse_qs(qs)
        except Exception:
            params = {}

        token_list = params.get("token") or params.get("access_token") or []
        token = token_list[0] if token_list else None

        # headers (Bearer)
        if not token:
            headers = {
                k.decode(): v.decode()
                for k, v in self.scope.get("headers", [])
            }
            auth = headers.get("authorization") or headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                token = auth.split(" ", 1)[1]

        # decode JWT
        if token:
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])

                user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
                role = payload.get("role")
                username = payload.get("username") or payload.get("name") or payload.get("preferred_username")

                if user_id and role:
                    # create lightweight user object
                    self.scope["user"] = SimpleUser(user_id, role, username)

            except (ExpiredSignatureError, InvalidTokenError):
                self.scope["user"] = None
            except Exception:
                self.scope["user"] = None

        return await self.inner(self.scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)