import json
import pytest
import asyncio

from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from django.test import override_settings

from quizzes.consumers.session_consumer import SessionConsumer
from quizzes.game.manager import SessionManager
from quizzes.game.scoreboard import Scoreboard
from app.settings_test import TEST_CHANNEL_LAYERS
@pytest.mark.asyncio
@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)

async def test_teacher_can_start_session():
    communicator = WebsocketCommunicator(
        SessionConsumer.as_asgi(),
        "/ws/session/ABC123/"
    )
    communicator.scope["user"] = type("User", (), {"id": 1, "is_teacher": True})()
    communicator.scope["url_route"] = {"kwargs": {"invite_code": "ABC123"}}
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({
        "action": "start_session"
    })

    response = await communicator.receive_json_from()

    assert response["type"] == "session_started"
    assert response["session_id"] == "ABC123"

    await communicator.disconnect()


@pytest.mark.asyncio
@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
async def test_student_join_and_scoreboard():
    """
    Тест подключения ученика, join_session и корректности Scoreboard.
    """
    communicator = WebsocketCommunicator(
        SessionConsumer.as_asgi(),
        "/ws/session/ABC123/"
    )
    communicator.scope["user"] = type("User", (), {"id": 1, "is_teacher": True})()
    communicator.scope["url_route"] = {"kwargs": {"invite_code": "ABC123"}}

    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({
        "action": "join_session",
        "nickname": "Alice"
    })

    res = await communicator.receive_json_from()
    assert res["type"] == "player_joined"
    assert res["nickname"] == "Alice"

    await communicator.send_json_to({"action": "get_leaderboard"})
    lb = await communicator.receive_json_from()

    assert lb["type"] == "leaderboard"
    assert lb["leaderboard"][0]["nickname"] == "Alice"
    assert lb["leaderboard"][0]["score"] == 0

    await communicator.disconnect()


@pytest.mark.asyncio
@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
async def test_submit_answer_and_score_added(monkeypatch):


    async def fake_get_correct_answer(*args, **kwargs):
        return {"is_correct": True}

    monkeypatch.setattr(SessionManager, "get_correct_answer", fake_get_correct_answer, raising=False)

    async def fake_save_answer(*args, **kwargs):
        return None

    monkeypatch.setattr(SessionManager, "save_answer", fake_save_answer, raising=False)

    communicator = WebsocketCommunicator(
        SessionConsumer.as_asgi(),
        "/ws/session/ABC123/"
    )
    communicator.scope["user"] = type("User", (), {"id": 1, "is_teacher": True})()
    communicator.scope["url_route"] = {"kwargs": {"invite_code": "ABC123"}}

    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({
        "action": "join_session",
        "nickname": "Bob"
    })
    await communicator.receive_json_from()  # player_joined

    await communicator.send_json_to({
        "action": "submit_answer",
        "question_id": 1,
        "response_time": 2.0
    })

    result = await communicator.receive_json_from()
    assert result["type"] == "answer_received"
    assert result["correct"] is True

    await communicator.send_json_to({"action": "get_leaderboard"})
    lb = await communicator.receive_json_from()

    assert lb["leaderboard"][0]["nickname"] == "Bob"
    assert lb["leaderboard"][0]["score"] > 0
    await communicator.disconnect()


@pytest.mark.asyncio
@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
async def test_broadcast_scoreboard():
    """
    Проверяем, что broadcast через group_send работает.
    """

    communicator = WebsocketCommunicator(
        SessionConsumer.as_asgi(),
        "/ws/session/ABC123/"
    )
    communicator.scope["user"] = type("User", (), {"id": 1, "is_teacher": True})()
    communicator.scope["url_route"] = {"kwargs": {"invite_code": "ABC123"}}

    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "session_ROOM22",
        {
            "type": "broadcast_scoreboard",
            "leaderboard": [{"nickname": "X", "score": 50}]
        }
    )

    msg = await communicator.receive_json_from()
    assert msg["type"] == "scoreboard_update"
    assert msg["leaderboard"][0]["nickname"] == "X"
    assert msg["leaderboard"][0]["score"] == 50

    await communicator.disconnect()