import json
from .redis_keys import PLAYERS

class Scoreboard:
    def __init__(self, redis):
        self.redis = redis

    async def add_player(self, session_id: str, player_id: str, nickname: str):
        key = PLAYERS.format(session_id=session_id)
        await self.redis.hset(key, player_id, json.dumps({"nickname": nickname, "score": 0}))

    async def remove_player(self, session_id: str, player_id: str):
        key = PLAYERS.format(session_id=session_id)
        await self.redis.hdel(key, player_id)

    async def add_score(self, session_id: str, player_id: str, points: int):
        key = PLAYERS.format(session_id=session_id)
        raw = await self.redis.hget(key, player_id)
        if not raw:
            return
        data = json.loads(raw)
        data["score"] = data.get("score", 0) + int(points)
        await self.redis.hset(key, player_id, json.dumps(data))
            
    async def get_leaderboard(self, session_id: str, top_n: int = 5):
        key = PLAYERS.format(session_id=session_id)
        raw = await self.redis.hgetall(key)
        out = []
        for pid, v in raw.items():
            if isinstance(v, bytes):
                try:
                    d = json.loads(v.decode())
                except Exception:
                    d = {"nickname": v.decode(), "score": 0}
            else:
                try:
                    d = json.loads(v)
                except Exception:
                    d = {"nickname": v, "score": 0}
            out.append({ "nickname": d.get("nickname"), "score": d.get("score", 0)})
        out.sort(key=lambda x: -x["score"])
        return out[:top_n] if top_n else out