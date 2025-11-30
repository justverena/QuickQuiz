import json
import time
import asyncio
from asgiref.sync import sync_to_async
from .redis_keys import SESSION_STATE, CURRENT_QUESTION, SESSION_QUESTIONS, SESSION_ANSWERS, PLAYERS, META_PREFIX
from django.db import transaction
from quizzes.models import Session as SessionModel, SessionPlayer, Answer as AnswerModel, Question as QuestionModel
_now = lambda: time.time()

class SessionManager:
    def __init__(self, redis):
        self.redis = redis

    async def create_state(self, session_id: str, quiz_id: str):
        key = SESSION_STATE.format(session_id=session_id)
        state = {"quiz_id": str(quiz_id), "current_question": -1, "status": "waiting", "started_at": None}
        await self.redis.set(key, json.dumps(state))

    async def get_state(self, session_id: str):
        raw = await self.redis.get(SESSION_STATE.format(session_id=session_id))
        return json.loads(raw) if raw else None

    async def set_state_field(self, session_id: str, field: str, value):
        key = SESSION_STATE.format(session_id=session_id)
        raw = await self.redis.get(key)
        state = json.loads(raw) if raw else {}
        state[field] = value
        await self.redis.set(key, json.dumps(state))

    async def store_questions(self, session_id: str, questions_list: list):
        """
        questions_list: list of dicts {question_id, text, options:[{id,text,index}], correct_index, type, points, timer}
        """
        await self.redis.set(SESSION_QUESTIONS.format(session_id=session_id), json.dumps(questions_list))

    async def get_all_questions(self, session_id: str):
        raw = await self.redis.get(SESSION_QUESTIONS.format(session_id=session_id))
        return json.loads(raw) if raw else []

    async def set_current_question(self, session_id: str, index: int):
        await self.redis.set(CURRENT_QUESTION.format(session_id=session_id), int(index))
        await self.set_state_field(session_id, "current_question", int(index))

    async def get_current_question(self, session_id: str) -> int:
        raw = await self.redis.get(CURRENT_QUESTION.format(session_id=session_id))
        try:
            return int(raw)
        except Exception:
            return -1

    async def save_answer(self, session_id: str, qidx: int, player_id: str, selected_options: list, ts: float = None) -> bool:
        """
        Save player's answer for question qidx.
        Returns True if saved, False if player already answered (duplicate).
        """
        key = SESSION_ANSWERS.format(session_id=session_id, qidx=qidx)
        exists = await self.redis.hexists(key, player_id)
        if exists:
            return False
        payload = {"selected": selected_options, "ts": (_now() if ts is None else ts)}
        await self.redis.hset(key, player_id, json.dumps(payload))
        return True

    async def get_answers_for_question(self, session_id: str, qidx: int) -> dict:
        key = SESSION_ANSWERS.format(session_id=session_id, qidx=qidx)
        raw = await self.redis.hgetall(key)
        out = {}
        for pid, v in raw.items():
            try:
                out[pid] = json.loads(v)
            except Exception:
                out[pid] = {"selected": v}
        return {k.decode() if isinstance(k, bytes) else k: v for k, v in out.items()}

    async def clear_answers_for_question(self, session_id: str, qidx: int):
        key = SESSION_ANSWERS.format(session_id=session_id, qidx=qidx)
        await self.redis.delete(key)

    async def set_meta(self, session_id: str, key: str, value):
        await self.redis.hset(META_PREFIX.format(session_id=session_id), key, json.dumps(value))

    async def get_meta(self, session_id: str, key: str):
        raw = await self.redis.hget(META_PREFIX.format(session_id=session_id), key)
        return json.loads(raw) if raw else None

    async def cleanup_session_keys(self, session_id: str):
        pattern = f"session:{session_id}:*"
        cur = b'0'
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)

    #persist to DB
    async def finalize_to_db(self, session_id: str, session_db_id):
        players_raw = await self.redis.hgetall(PLAYERS.format(session_id=session_id))

        leaderboard = []
        for pid, v in players_raw.items():
            try:
                d = json.loads(v)
            except Exception:
                d = {"nickname": v, "score": 0}
            leaderboard.append({"player_id": pid.decode() if isinstance(pid, bytes) else pid,
                                "nickname": d["nickname"],
                                "score": d["score"]})

        questions = await self.get_all_questions(session_id)

        answers_per_question = {}
        for qidx, q in enumerate(questions):
            key = SESSION_ANSWERS.format(session_id=session_id, qidx=qidx)
            raw_ans = await self.redis.hgetall(key)
            parsed = {}
            for pid, payload in raw_ans.items():
                pid = pid.decode() if isinstance(pid, bytes) else pid
                try:
                    parsed[pid] = json.loads(payload)
                except Exception:
                    parsed[pid] = {"selected": []}
            answers_per_question[qidx] = parsed


        @sync_to_async
        def _persist():
            session_db = SessionModel.objects.get(id=session_db_id)

            with transaction.atomic():

                session_db.status = "finished"
                session_db.save()

                for row in leaderboard:
                    SessionPlayer.objects.create(
                        session=session_db,
                        student_id=row["player_id"],
                        nickname=row["nickname"],
                        final_score=row["score"]
                    )

                for qidx, q in enumerate(questions):
                    try:
                        q_obj = QuestionModel.objects.get(id=q["question_id"])
                    except QuestionModel.DoesNotExist:
                        continue

                    ans_map = answers_per_question.get(qidx, {})

                    for pid, rec in ans_map.items():
                        selected = rec.get("selected", [])
                        is_correct = False

                        try:
                            if q["type"] == "single":
                                is_correct = selected and int(selected[0]) == int(q["correct_index"])
                            else:
                                is_correct = any(int(s) == int(q["correct_index"]) for s in selected)
                        except:
                            pass

                        AnswerModel.objects.create(
                            session=session_db,
                            student_id=pid,
                            question=q_obj,
                            selected_options=selected,
                            is_correct=is_correct
                        )

        await _persist()