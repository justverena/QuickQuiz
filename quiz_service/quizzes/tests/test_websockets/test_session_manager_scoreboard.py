import pytest
import fakeredis.aioredis as fake_redis
import asyncio
from quizzes.game.manager import SessionManager
from quizzes.game.scoreboard import Scoreboard

@pytest.mark.asyncio
async def test_session_manager_create_get_state():
    r = await fake_redis.FakeRedis.from_url("redis://localhost")
    sm = SessionManager(r)
    await sm.create_state("sess1", "quiz1")
    st = await sm.get_state("sess1")
    assert st["quiz_id"] == "quiz1"
    assert st["status"] == "waiting"
    await r.close()

@pytest.mark.asyncio
async def test_save_answer_and_prevent_duplicate():
    r = await fake_redis.FakeRedis.from_url("redis://localhost")
    sm = SessionManager(r)
    # create and save
    saved = await sm.save_answer("sess2", 0, "p1", ["1"])
    assert saved is True
    saved2 = await sm.save_answer("sess2", 0, "p1", ["2"])
    assert saved2 is False  # duplicate prevented
    answers = await sm.get_answers_for_question("sess2", 0)
    assert "p1" in answers
    await r.close()

@pytest.mark.asyncio
async def test_scoreboard_add_and_leaderboard():
    r = await fake_redis.FakeRedis.from_url("redis://localhost")
    sb = Scoreboard(r)
    await sb.add_player("sess3", "p1", "Alice")
    await sb.add_player("sess3", "p2", "Bob")
    await sb.add_score("sess3", "p1", 10)
    await sb.add_score("sess3", "p2", 20)
    lb = await sb.get_leaderboard("sess3", top_n=2)
    assert lb[0]["player_id"] == "p2" and lb[0]["score"] == 20
    assert lb[1]["player_id"] == "p1" and lb[1]["score"] == 10
    await r.close()