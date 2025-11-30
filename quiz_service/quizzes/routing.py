from django.urls import re_path
from quizzes.consumers.session_consumer import SessionConsumer
from quizzes.middleware import JWTAuthMiddlewareStack

websocket_urlpatterns = [
    re_path(
        r"ws/session/(?P<invite_code>[A-Za-z0-9]+)/?$",
        JWTAuthMiddlewareStack(SessionConsumer.as_asgi())
    )
]   