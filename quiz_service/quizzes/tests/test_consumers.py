import uuid
import jwt
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.conf import settings
from channels.db import database_sync_to_async
import asyncio
from quizzes.consumers import SessionConsumer
from quizzes.models import Quiz, Question, Option, Session, Answer

class TestSessionConsumer(TransactionTestCase):
    async_capable = True

    def setUp(self):
        self.teacher_id = uuid.uuid4()
        self.student_id = uuid.uuid4()
        self.student2_id = uuid.uuid4()

        self.quiz = Quiz.objects.create(
            title="Test Quiz",
            description="Desc",
            teacher_id=self.teacher_id
        )

        self.question = Question.objects.create(
            quiz_id=self.quiz,
            text="First question?",
            type="single",
            points=1,
            correct_option_index=0,
            timer=30,
            index=0
        )
        self.option1 = Option.objects.create(question=self.question, text="Option 1", index=0)
        self.option2 = Option.objects.create(question=self.question, text="Option 2", index=1)

        self.session = Session.objects.create(
            quiz_id=self.quiz,
            teacher_id=uuid.uuid4(),
            invite_code="ABCDE",
            current_question_index=self.question.index,
            status="in_progress"
        )

        self.token_student = self.make_jwt_token("student", self.student_id)
        self.token_student2 = self.make_jwt_token("student", self.student2_id)
        self.token_teacher = self.make_jwt_token("teacher", self.teacher_id)

    def make_jwt_token(self, role, user_id):
        payload = {"sub": str(user_id), "role": role}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    async def test_connect(self):
        path = f"/ws/session/{self.session.invite_code}/"
        headers = [(b"authorization", f"Bearer {self.token_student}".encode())]

        communicator = WebsocketCommunicator(SessionConsumer.as_asgi(), path, headers=headers)
        communicator.scope["url_route"] = {"kwargs": {"invite_code": self.session.invite_code}}

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "info")
        self.assertIn("Connected to session", response["message"])

        await communicator.disconnect()


# вот этот тест ругался, не я TоT
    async def test_answer_message_correct(self):
        path = f"/ws/session/{self.session.invite_code}/"
        headers = [(b"authorization", f"Bearer {self.token_student}".encode())]

        communicator = WebsocketCommunicator(SessionConsumer.as_asgi(), path, headers=headers)
        communicator.scope["url_route"] = {"kwargs": {"invite_code": self.session.invite_code}}
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({
            "action": "answer",
            "student_id": str(self.student_id),
            "question_id": str(self.question.id),
            "selected_options": [str(self.option1.id)],
            "response_time": 3.0
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "answer")
        self.assertEqual(response["student_id"], str(self.student_id))
        
        expected_is_correct = self.option1.index == self.question.correct_option_index
        self.assertEqual(response["is_correct"], expected_is_correct)
        
        answer = await database_sync_to_async(Answer.objects.get)(
            student_id=self.student_id, 
            question=self.question)
        self.assertEqual(answer.is_correct, expected_is_correct)

        await communicator.disconnect()

    async def test_multiple_students_receive_broadcast(self):
        path = f"/ws/session/{self.session.invite_code}/"
        comm1 = WebsocketCommunicator(SessionConsumer.as_asgi(), path, headers=[(b"authorization", f"Bearer {self.token_student}".encode())])
        comm2 = WebsocketCommunicator(SessionConsumer.as_asgi(), path, headers=[(b"authorization", f"Bearer {self.token_student2}".encode())])

        comm1.scope["url_route"] = comm2.scope["url_route"] = {"kwargs": {"invite_code": self.session.invite_code}}
        await comm1.connect()
        await comm2.connect()
        await comm1.receive_json_from()
        await comm2.receive_json_from()

        await comm1.send_json_to({
            "action": "answer",
            "student_id": str(self.student_id),
            "question_id": str(self.question.id),
            "selected_options": [str(self.option1.id)],
            "response_time": 2.0
        })

        resp1 = await comm1.receive_json_from()
        resp2 = await comm2.receive_json_from()
        self.assertEqual(resp1["type"], "answer")
        self.assertEqual(resp2["type"], "answer")
        self.assertEqual(resp1["student_id"], str(self.student_id))
        self.assertEqual(resp2["student_id"], str(self.student_id))

        await comm1.disconnect()
        await comm2.disconnect()

    async def test_teacher_sees_all_answers(self):
        path_student = f"/ws/session/{self.session.invite_code}/"
        path_teacher = f"/ws/session/{self.session.invite_code}/"
        student_comm = WebsocketCommunicator(SessionConsumer.as_asgi(), path_student, headers=[(b"authorization", f"Bearer {self.token_student}".encode())])
        teacher_comm = WebsocketCommunicator(SessionConsumer.as_asgi(), path_teacher, headers=[(b"authorization", f"Bearer {self.token_teacher}".encode())])

        student_comm.scope["url_route"] = teacher_comm.scope["url_route"] = {"kwargs": {"invite_code": self.session.invite_code}}
        await student_comm.connect()
        await teacher_comm.connect()
        await student_comm.receive_json_from()
        await teacher_comm.receive_json_from()

        await student_comm.send_json_to({
            "action": "answer",
            "student_id": str(self.student_id),
            "question_id": str(self.question.id),
            "selected_options": [str(self.option1.id)],
            "response_time": 2.0
        })

        resp_teacher = await teacher_comm.receive_json_from()
        self.assertEqual(resp_teacher["type"], "answer")
        self.assertEqual(resp_teacher["student_id"], str(self.student_id))

        await student_comm.disconnect()
        await teacher_comm.disconnect()

    async def test_answer_nonexistent_question(self):
        path = f"/ws/session/{self.session.invite_code}/"
        comm = WebsocketCommunicator(SessionConsumer.as_asgi(), path, headers=[(b"authorization", f"Bearer {self.token_student}".encode())])
        comm.scope["url_route"] = {"kwargs": {"invite_code": self.session.invite_code}}
        await comm.connect()
        await comm.receive_json_from()

        await comm.send_json_to({
            "action": "answer",
            "student_id": str(self.student_id),
            "question_id": str(uuid.uuid4()),
            "selected_options": [str(self.option1.id)],
            "response_time": 2.0
        })

        response = await comm.receive_json_from()
        self.assertEqual(response["type"], "error")
        self.assertIn("not found", response["message"])

        await comm.disconnect()

    async def test_invalid_token_or_invite(self):
        path = f"/ws/session/WRONGCODE/"
        comm = WebsocketCommunicator(SessionConsumer.as_asgi(), path)
        comm.scope["url_route"] = {"kwargs": {"invite_code": "WRONGCODE"}}

        connected, subprotocol = await comm.connect()
        self.assertFalse(connected)
        try:
            await comm.disconnect()
        except asyncio.CancelledError:
            pass

    # async def test_session_status_after_next_question(self):
    #     question2 = await database_sync_to_async(Question.objects.create)(
    #         quiz_id=self.quiz,
    #         text="Second question?",
    #         correct_option_index = 1,
    #         timer = 30,
    #         type="single",
    #         points=1,
    #         index=1
            
    #     )
    #     await database_sync_to_async(Option.objects.create)(question=question2, text="Option 1", index=1)
        
    #     next_question = await database_sync_to_async(
    #         lambda: list (self.quiz.questions.all().order_by("index"))[1]
    #     )()
        
    #     path = f"/ws/session/{self.session.invite_code}/"
    #     comm = WebsocketCommunicator(
    #         SessionConsumer.as_asgi(),
    #         path,
    #         headers=[(b"authorization", f"Bearer {self.token_teacher}".encode())]
    #     )
    #     comm.scope["url_route"] = {"kwargs": {"invite_code": self.session.invite_code}}
    #     await comm.connect()
    #     await comm.receive_json_from()

    #     await comm.send_json_to({
    #         "action": "next_question",
    #         "question_id": str(next_question.id)
    #     })

    #     while True:
    #         response = await comm.receive_json_from()
    #         if response.get("action") == "next_question":
    #             break
    #         await asyncio.sleep(0.01)


    #     self.assertEqual(response["action"], "next_question")
    #     self.assertEqual(response["question_id"], str(question2.id))
    #     self.assertEqual(response["text"], question2.text)
    #     self.assertIn("options", response)
    #     self.assertTrue(len(response["options"]) > 0)

    #     session = await database_sync_to_async(Session.objects.get)(id=self.session.id)
    #     self.assertEqual(session.current_question_index, next_question.id)
    #     self.assertEqual(session.status, "in_progress")

    #     await comm.disconnect()

    async def test_multiple_students_receive_next_question(self):
        question2 = await database_sync_to_async(Question.objects.create)(
            quiz_id=self.quiz,
            text="Next question?",
            correct_option_index = 1,
            timer = 30,
            type="single",
            points=1
        )
        await database_sync_to_async(Option.objects.create)(question=question2, text="Opt 1", index=question2.correct_option_index)

        path = f"/ws/session/{self.session.invite_code}/"
        comm1 = WebsocketCommunicator(
            SessionConsumer.as_asgi(),
            path,
            headers=[(b"authorization", f"Bearer {self.token_student}".encode())]
        )
        comm2 = WebsocketCommunicator(
            SessionConsumer.as_asgi(),
            path,
            headers=[(b"authorization", f"Bearer {self.token_student2}".encode())]
        )
        comm1.scope["url_route"] = comm2.scope["url_route"] = {"kwargs": {"invite_code": self.session.invite_code}}

        await comm1.connect()
        await comm2.connect()
        await comm1.receive_json_from()
        await comm2.receive_json_from()

        teacher_comm = WebsocketCommunicator(
            SessionConsumer.as_asgi(),
            path,
            headers=[(b"authorization", f"Bearer {self.token_teacher}".encode())]
        )
        teacher_comm.scope["url_route"] = {"kwargs": {"invite_code": self.session.invite_code}}
        await teacher_comm.connect()
        await teacher_comm.receive_json_from()

        await teacher_comm.send_json_to({
            "action": "next_question",
            "question_id": str(question2.id)
        })

        await asyncio.sleep(0.05)

        async def get_next_question_response(comm):
            while True:
                resp = await comm.receive_json_from()
                if resp.get("action") == "next_question":
                    return resp

        
        resp1 = await get_next_question_response(comm1)
        resp2 = await get_next_question_response(comm2)
        
        session = await database_sync_to_async(Session.objects.get)(id=self.session.id)
        current_index = session.current_question_index
        next_question = await database_sync_to_async(
            lambda: list(self.quiz.questions.all().order_by("index"))[current_index]
        )()
        self.assertEqual(resp1["action"], "next_question")
        self.assertEqual(resp2["action"], "next_question")
        self.assertEqual(resp1["question_id"], str(next_question.id))

        await comm1.disconnect()
        await comm2.disconnect()
        await teacher_comm.disconnect()