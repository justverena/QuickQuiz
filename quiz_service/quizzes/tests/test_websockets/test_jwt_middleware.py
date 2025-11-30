import pytest
import jwt
from django.conf import settings
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import re_path
from quizzes.middleware import JWTAuthMiddlewareStack
from channels.layers import get_channel_layer

# A tiny websocket app that on connect sends scope['user'] as JSON then closes
async def simple_ws_app(scope, receive, send):
    assert scope["type"] == "websocket"
    await send({
        "type": "websocket.accept"
    })
    user = scope.get("user")
    await send({
        "type": "websocket.send",
        "text": json.dumps({"user": user})
    })
    await send({
        "type": "websocket.close"
    })

import json

# Build a routing that uses our simple app (wrapped by middleware)
application = JWTAuthMiddlewareStack(
    URLRouter([
        re_path(r"ws/test/$", simple_ws_app),
    ])
)

@pytest.mark.asyncio
async def test_middleware_accepts_valid_token(monkeypatch):
    payload = {"sub": "user-123", "role": "student", "username": "alice"}
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    communicator = WebsocketCommunicator(application, "/ws/test/?token=" + token)
    connected, _ = await communicator.connect()
    assert connected
    msg = await communicator.receive_json_from()
    assert msg["user"] is not None
    assert msg["user"]["id"] == "user-123"
    assert msg["user"]["role"] == "student"
    await communicator.disconnect()

@pytest.mark.asyncio
async def test_middleware_rejects_invalid_token(monkeypatch):
    bad = "invalid.token.here"
    communicator = WebsocketCommunicator(application, "/ws/test/?token=" + bad)
    connected, _ = await communicator.connect()
    # still accepts connection, but scope['user'] should be None
    assert connected
    msg = await communicator.receive_json_from()
    assert msg["user"] is None
    await communicator.disconnect()