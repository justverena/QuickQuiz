import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Session, Question, Answer
from django.core.exceptions import ObjectDoesNotExist

class SessionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.invite_code = self.scope['url_route']['kwargs']['invite_code']

        try:
            self.session = await sync_to_async(Session.objects.get)(invite_code=self.invite_code)
        except ObjectDoesNotExist:
            await self.close(code=4001)
            return

        self.room_group_name = f"session_{self.invite_code}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.send_json({
            "type": "info",
            "message": f"Connected to session {self.invite_code}"
        })

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "answer":
            await self.handle_answer(data)
        elif action == "next_question":
            await self.handle_next_question(data)

    async def handle_answer(self, data):
        student_id = data["student_id"]
        question_id = data["question_id"]
        selected_options = data.get("selected_options", [])

        try:
            question = await sync_to_async(Question.objects.get)(id=question_id)
        except ObjectDoesNotExist:
            await self.send_json({
                "type": "error",
                "message": f"Question with id {question_id} not found"
            })
            return

        session = self.session

        correct_ids = list(map(str, await sync_to_async(list)(
            question.options.filter(is_correct=True).values_list("id", flat=True)
        )))
        is_correct = set(selected_options) == set(correct_ids)

        await sync_to_async(Answer.objects.create)(
            session=session,
            student_id=student_id,
            question=question,
            selected_options=selected_options,
            is_correct=is_correct,
            response_time=data.get("response_time", 0)
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_message",
                "message": {
                    "type": "answer",
                    "student_id": student_id,
                    "is_correct": is_correct
                },
            }
        )
    
    async def handle_next_question(self, data):
        session = self.session
        
        all_questions = await sync_to_async(lambda: list(session.quiz.questions.all().order_by("id")))()

        if not all_questions:
            await self.send_json({
                "type": "error",
                "message": "No questions available in this quiz"
            })
            return

        current_question = await sync_to_async(lambda: session.current_question)()

        if current_question:
            try:
                current_index = next(i for i, q in enumerate(all_questions) if q.id == current_question.id)
                next_index = current_index + 1
            except StopIteration:
                next_index = 0
        else:
            next_index = 0

        if next_index >= len(all_questions):
            session.status = "finished"
            await sync_to_async(session.save)()
            await self.send_json({
                "type": "end_session",
                "message": "Quiz finished!"
            })
            return

        next_question = all_questions[next_index]

        session.current_question = next_question
        session.status = "in_progress"
        await sync_to_async(session.save)()

        options = await sync_to_async(lambda: list(next_question.options.all()))()
        options_payload = [{"id": str(opt.id), "text": opt.text} for opt in options]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_message",
                "message": {
                    "action": "next_question",
                    "question_id": str(next_question.id),
                    "text": next_question.text,
                    "options": options_payload
                },
            }
        )

    async def broadcast_message(self, event):
        await self.send_json(event["message"])