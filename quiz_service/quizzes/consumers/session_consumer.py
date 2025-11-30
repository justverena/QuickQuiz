import json
import asyncio
import time
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import redis.asyncio as aioredis
from quizzes.game.manager import SessionManager
from quizzes.game.scoreboard import Scoreboard
from quizzes.game.redis_keys import CURRENT_QUESTION, SESSION_QUESTIONS, SESSION_ANSWERS, PLAYERS, SESSION_STATE
from quizzes.models import Question, Option, Session as SessionModel
from asgiref.sync import sync_to_async

_now = lambda: time.time()

def compute_points(base_points: int, time_limit: float, response_time: float, correct: bool, bonus_factor: float = 0.5, min_bonus: int = 0):
    if not correct:
        return 0
    speed_fraction = max(0.0, (time_limit - response_time) / time_limit) if time_limit > 0 else 0.0
    speed_bonus = int(base_points * speed_fraction * bonus_factor)
    return int(base_points + max(min_bonus, speed_bonus))

class SessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.invite_code = self.scope['url_route']['kwargs']['invite_code']
            user = self.scope.get('user')
            if not user:
                await self.close(code=4001)
                return
            self.user = user
            self.user_id = str(user.id)
            self.role = getattr(user, 'role', None)
            self.nickname = getattr(user, 'username', None) or f"Player_{self.user_id[:6]}"
            self.room_group_name = f"session_{self.invite_code}"

            # redis and managers
            self.redis = await aioredis.from_url(settings.REDIS_GAME_STATE, decode_responses=True)
            self.manager = SessionManager(self.redis)
            self.scoreboard = Scoreboard(self.redis)

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            

            self.session_id = await sync_to_async(lambda: SessionModel.objects.get(invite_code=self.invite_code).id)()

            await self.accept()

            await self._send_initial_state()

            if self.role == 'student':
                await self.scoreboard.add_player(self.session_id, self.user_id, self.nickname)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {"type": "player_joined", "player_id": self.user_id, "nickname": self.nickname}
                )

        except Exception:
            traceback.print_exc()
            await self.close(code=1011)

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
        except Exception:
            return await self.send_json({"type": "error", "message": "invalid_json"})

        action = data.get("action")
        payload = data.get("payload", {})

        if action == "start_session" and self.role == "teacher":
            await self._handle_start_session(payload)
        elif action == "next_question" and self.role == "teacher":
            await self._handle_next_question(payload)
        elif action == "submit_answer" and self.role == "student":
            await self._handle_submit_answer(payload)
        elif action == "get_leaderboard":
            lb = await self.scoreboard.get_leaderboard(self.session_id, top_n=10)
            await self.send_json({"type": "leaderboard", "leaderboard": lb})
        else:
            await self.send_json({"type": "error", "message": "forbidden_or_unknown_action"})

    async def send_json(self, data):
        try:
            await self.send(text_data=json.dumps(data))
        except Exception:
            pass

    async def _send_initial_state(self):
        state = await self.manager.get_state(self.session_id)
        current_q = await self.manager.get_current_question(self.session_id)
        questions = await self.manager.get_all_questions(self.session_id)
        leaderboard = await self.scoreboard.get_leaderboard(self.session_id, top_n=10)
        await self.send_json({
            "type": "initial_state",
            "state": state,
            "current_question_index": current_q,
            "questions_count": len(questions),
            "leaderboard": leaderboard
        })
        if state and state.get("status") == "question_active" and 0 <= current_q < len(questions):
            q = questions[current_q]
            teacher_payload = q.copy(); teacher_payload["question_index"] = current_q
            student_payload = q.copy(); student_payload.pop("correct_index", None); student_payload["quiz_index"] = current_q

            if self.role == "teacher":
                await self.send_json({"type":"question_started","question_index": current_q, "question": teacher_payload})
            else:
                await self.send_json({"type":"question_started","question_index": current_q, "question": student_payload})

    #handlers
    async def _handle_start_session(self, payload):
        try:
            session_db = await sync_to_async(SessionModel.objects.get)(id=self.session_id)
        except SessionModel.DoesNotExist:
            return await self.send_json({"type": "error", "message": "session_not_found"})

        def get_questions_from_db(quiz_id):
            q_objs = Question.objects.filter(quiz_id=quiz_id).order_by("index").prefetch_related("options")
            questions_list = []
            for q in q_objs:
                questions_list.append({
                    "question_id": str(q.id),
                    "text": q.text,
                    "options": [{"id": str(o.id), "text": o.text, "index": o.index} for o in q.options.all()],
                    "correct_index": q.correct_option_index,
                    "type": q.type,
                    "points": q.points,
                    "timer": q.timer
                })
            return questions_list

        questions = await sync_to_async(get_questions_from_db)(session_db.quiz_id)
        await self.manager.store_questions(self.session_id, questions)
        await self.manager.set_state_field(self.session_id, "status", "running")
        await self.manager.set_state_field(self.session_id, "started_at", _now())

        await self._start_question(0)

    async def _handle_next_question(self, payload):
        current = await self.manager.get_current_question(self.session_id)
        questions = await self.manager.get_all_questions(self.session_id)
        next_idx = current + 1
        if next_idx >= len(questions):
            await self._finish_game()
        else:
            await self._start_question(next_idx)

    async def _start_question(self, qidx: int):
        questions = await self.manager.get_all_questions(self.session_id)
        if not (0 <= qidx < len(questions)):
            return
        q = questions[qidx]
        await self.manager.set_current_question(self.session_id, qidx)
        await self.manager.clear_answers_for_question(self.session_id, qidx)
        await self.manager.set_state_field(self.session_id, "status", "question_active")
        await self.manager.set_state_field(self.session_id, "question_started_at", _now())

        teacher_payload = q.copy()
        teacher_payload["question_index"] = qidx

        student_payload = q.copy()
        student_payload.pop("correct_index", None)
        student_payload["quiz_index"] = qidx 

        await self.channel_layer.group_send(self.room_group_name,{
            "type": "broadcast_question_started",
            "teacher_payload": teacher_payload,
            "student_payload": student_payload
            })
        
        if getattr(self, "_timer_task", None):
            self._timer_task.cancel()
        self._timer_task = asyncio.create_task(self._question_timer_worker(qidx, q.get("timer", 15)))

    async def _question_timer_worker(self, qidx: int, duration: int):
        start_ts = _now()
        end_ts = start_ts + float(duration)
        interval = 30
        while True:
            time_left = max(0, end_ts - _now())
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "broadcast_time_left", "time_left": int(time_left), "question_index": qidx}
            )
            if time_left <= 0:
                break
            await asyncio.sleep(min(interval, time_left))
        try:
            await self._finalize_question(qidx)
        except Exception:
            traceback.print_exc()

    async def _finalize_question(self, qidx: int):
        questions = await self.manager.get_all_questions(self.session_id)
        if not (0 <= qidx < len(questions)):
            return
        q = questions[qidx]
        answers = await self.manager.get_answers_for_question(self.session_id, qidx)
        per_player_results = []
        meta_qstart = await self.manager.get_meta(self.session_id, "question_started_at")
        if meta_qstart:
            qstart = meta_qstart
        else:
            state = await self.manager.get_state(self.session_id)
            qstart = state.get("started_at") if state else _now()


        for pid, rec in answers.items():
            selected = rec.get("selected", [])
            ts = rec.get("ts", _now())
            response_time = max(0.0, ts - qstart)

            correct = False
            try:
                if q["type"] == "single" and selected and int(selected[0]) == int(q.get("correct_index", -1)):
                    correct = True
                elif selected and any(int(s) == int(q.get("correct_index", -1)) for s in selected):
                    correct = True
            except Exception:
                correct = False

            delta = compute_points(int(q.get("points", 1)), float(q.get("timer", 15)), response_time, correct)
            if delta > 0:
                await self.scoreboard.add_score(self.session_id, pid, delta)
            per_player_results.append({"player_id": pid, "selected": selected, "correct": correct, "delta": delta, "response_time": response_time})


        await self.manager.set_state_field(self.session_id, "status", "question_closed")
        
        await self.channel_layer.group_send(self.room_group_name, {"type": "broadcast_question_results", "payload": {"question_index": qidx, "results": per_player_results}})

        correct_index = q.get("correct_index")
        await self.channel_layer.group_send(self.room_group_name,{"type": "broadcast_question_results_summary", "payload": {"question_index": qidx, "correct_index": correct_index}})

        leaderboard = await self.scoreboard.get_leaderboard(self.session_id, top_n=10)

        await self.channel_layer.group_send(self.room_group_name, {"type": "broadcast_scoreboard", "leaderboard": leaderboard})

    async def _finish_game(self):
        await self.manager.set_state_field(self.session_id, "status", "finished")
        leaderboard = await self.scoreboard.get_leaderboard(self.session_id, top_n=10)
        await self.channel_layer.group_send(self.room_group_name, {"type": "broadcast_game_finished", "leaderboard": leaderboard})
        try:
            await self.manager.finalize_to_db(self.session_id, self.session_id)
        except Exception:
            traceback.print_exc()
        await self.manager.cleanup_session_keys(self.session_id)

    async def _handle_submit_answer(self, payload):
        qidx = payload.get("question_index")
        option_index = payload.get("option_index")
        if qidx is None or option_index is None:
            return await self.send_json({"type": "error", "message": "missing_question_or_option_index"})
        selected = [int(option_index)]
        key = SESSION_ANSWERS.format(session_id=self.session_id, qidx=qidx)
        if await self.redis.hexists(key, self.user_id):
            return await self.send_json({"type": "error", "message": "already_answered"})
        saved = await self.manager.save_answer(self.session_id, int(qidx), self.user_id, selected, ts=_now())
        if not saved:
            return await self.send_json({"type": "error", "message": "already_answered"})
        await self.send_json({"type": "answer_ack", "question_index": qidx})
        await self.channel_layer.group_send(self.room_group_name, {"type": "broadcast_student_answered", "player_id": self.user_id, "question_index": qidx})

    #broadcasts
    async def player_joined(self, event):
        if self.role == "teacher":
            await self.send_json({"type": "student_joined", "player_id": event["player_id"], "nickname": event["nickname"]})

    async def broadcast_question_started(self, event):
        if self.role == "teacher":
            await self.send_json({
                "type": "question_started",
                "question_index": event["teacher_payload"]["question_index"],
                "question": event["teacher_payload"]
            })
        elif self.role == "student":
            await self.send_json({
                "type": "question_started",
                "question_index": event["student_payload"]["quiz_index"],
                "question": event["student_payload"]
            })

    async def broadcast_time_left(self, event):
        await self.send_json({"type": "time_left", "time_left": event["time_left"], "question_index": event.get("question_index")})

    async def broadcast_student_answered(self, event):
        if self.role == "teacher":
            await self.send_json({"type": "student_answered", "player_id": event["player_id"], "question_index": event["question_index"]})

    async def broadcast_question_results(self, event):
        if self.role == "teacher":
            await self.send_json({"type": "question_results", "payload": event["payload"]})
    
    async def broadcast_question_results_summary(self, event):
        if self.role == "student":
            await self.send_json({
                "type": "question_results_summary",
                "payload": {"question_index": event["payload"]["question_index"], "correct_index": event["payload"].get("correct_index")}
            })

    async def broadcast_scoreboard(self, event):
        await self.send_json({"type": "scoreboard_update", "leaderboard": event["leaderboard"]})

    async def broadcast_game_finished(self, event):
        await self.send_json({"type": "game_finished", "leaderboard": event["leaderboard"]})