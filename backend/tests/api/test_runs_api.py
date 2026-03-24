from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.v1 import runs as runs_router
from app.db.models.runs import RunMode, RunStatus
from app.main import create_app
from app.services.runs.schemas import AnswerResult, QuestionData, Settlement, SubmitAnswerResult


@dataclass
class FakeRun:
    id: UUID
    user_id: UUID
    document_id: UUID | None
    mode: RunMode
    status: RunStatus
    score: int
    total_questions: int
    correct_answers: int
    combo_count: int
    started_at: datetime
    ended_at: datetime | None = None


class FakeRunService:
    def __init__(self) -> None:
        self.runs: dict[UUID, FakeRun] = {}
        self.questions: dict[UUID, list[QuestionData]] = {}
        self.answers: dict[UUID, list[AnswerResult]] = {}
        self.settlements: dict[UUID, Settlement] = {}

    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID,
        mode: RunMode,
        question_count: int,
    ) -> tuple[FakeRun, list[QuestionData]]:
        run_id = uuid4()
        questions = [
            QuestionData(
                id=uuid4(),
                document_id=document_id,
                question_text=f"Question {i + 1}?",
                question_type="single_choice",
                options=[
                    {"id": str(uuid4()), "text": "A"},
                    {"id": str(uuid4()), "text": "B"},
                    {"id": str(uuid4()), "text": "C"},
                    {"id": str(uuid4()), "text": "D"},
                ],
                correct_option_ids=[uuid4()],
                difficulty=1,
            )
            for i in range(question_count)
        ]
        run = FakeRun(
            id=run_id,
            user_id=user_id,
            document_id=document_id,
            mode=mode,
            status=RunStatus.RUNNING,
            score=0,
            total_questions=question_count,
            correct_answers=0,
            combo_count=0,
            started_at=datetime.now(UTC),
        )
        self.runs[run_id] = run
        self.questions[run_id] = questions
        return run, questions

    async def get_run(self, run_id: UUID, user_id: UUID | None = None) -> FakeRun:
        run = self.runs.get(run_id)
        if not run:
            raise ValueError("Run not found")
        return run

    async def list_runs(self, user_id: UUID) -> list[FakeRun]:
        return [r for r in self.runs.values() if r.user_id == user_id]

    async def submit_answer(
        self,
        run_id: UUID,
        question_id: UUID,
        selected_option_ids: list[UUID],
        answer_time_ms: int | None = None,
    ) -> SubmitAnswerResult:
        run = await self.get_run(run_id)
        if run.status != RunStatus.RUNNING:
            raise ValueError("Run not running")

        questions = self.questions.get(run_id, [])
        question = next((q for q in questions if q.id == question_id), None)
        if not question:
            raise ValueError("Question not in run")
        is_correct = question.correct_option_ids[0] in selected_option_ids
        answer = AnswerResult(
            id=uuid4(),
            run_id=run_id,
            question_id=question_id,
            selected_option_ids=selected_option_ids,
            is_correct=is_correct,
            time_spent_ms=answer_time_ms,
            created_at=datetime.now(UTC),
        )
        if run_id not in self.answers:
            self.answers[run_id] = []
        self.answers[run_id].append(answer)
        run.correct_answers += 1 if is_correct else 0
        run.combo_count = run.combo_count + 1 if is_correct else 0
        run.score = run.correct_answers * 10
        settlement = None
        if len(self.answers[run_id]) >= run.total_questions:
            run.status = RunStatus.COMPLETED
            run.ended_at = datetime.now(UTC)
            settlement = Settlement(
                run_id=run_id,
                xp_earned=run.score,
                coins_earned=run.score // 10,
                combo_max=run.combo_count,
                accuracy=run.correct_answers / run.total_questions,
                correct_count=run.correct_answers,
                total_count=run.total_questions,
            )
            self.settlements[run_id] = settlement
        return SubmitAnswerResult(
            answer=answer,
            is_correct=is_correct,
            run=run,
            settlement=settlement,
        )

    async def get_settlement(self, run_id: UUID) -> Settlement:
        run = await self.get_run(run_id)
        if run.status != RunStatus.COMPLETED:
            raise ValueError("Run not completed")
        settlement = self.settlements.get(run_id)
        if not settlement:
            raise ValueError("Settlement not found")
        return settlement


def create_test_client(user_id: UUID) -> TestClient:
    app = create_app()
    fake_service = FakeRunService()
    app.dependency_overrides[runs_router.get_current_user_id] = lambda: user_id
    app.dependency_overrides[runs_router.get_run_service] = lambda: fake_service
    return TestClient(app)


class TestRunsAPI:
    def test_create_run_returns_run_with_questions(self) -> None:
        user_id = uuid4()
        doc_id = uuid4()
        client = create_test_client(user_id)
        response = client.post(
            "/api/v1/runs",
            json={
                "document_id": str(doc_id),
                "mode": "endless",
                "question_count": 5,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert "run_id" in body
        assert body["mode"] == "endless"
        assert body["status"] == "running"
        assert len(body["questions"]) == 5

    def test_create_run_validates_question_count(self) -> None:
        user_id = uuid4()
        doc_id = uuid4()
        client = create_test_client(user_id)
        response = client.post(
            "/api/v1/runs",
            json={
                "document_id": str(doc_id),
                "mode": "endless",
                "question_count": 0,
            },
        )
        assert response.status_code == 422

    def test_submit_answer_returns_result(self) -> None:
        user_id = uuid4()
        doc_id = uuid4()
        client = create_test_client(user_id)
        create_response = client.post(
            "/api/v1/runs",
            json={
                "document_id": str(doc_id),
                "mode": "endless",
                "question_count": 3,
            },
        )
        run_id = create_response.json()["run_id"]
        questions = create_response.json()["questions"]
        question_id = questions[0]["id"]
        response = client.post(
            f"/api/v1/runs/{run_id}/answers",
            json={
                "question_id": question_id,
                "selected_option_ids": [str(uuid4())],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "is_correct" in body
        assert "answer" in body
        assert "run" in body

    def test_submit_answer_returns_settlement_on_completion(self) -> None:
        user_id = uuid4()
        doc_id = uuid4()
        client = create_test_client(user_id)
        create_response = client.post(
            "/api/v1/runs",
            json={
                "document_id": str(doc_id),
                "mode": "endless",
                "question_count": 1,
            },
        )
        run_id = create_response.json()["run_id"]
        questions = create_response.json()["questions"]
        question_id = questions[0]["id"]
        response = client.post(
            f"/api/v1/runs/{run_id}/answers",
            json={
                "question_id": question_id,
                "selected_option_ids": [str(uuid4())],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["settlement"] is not None
        assert body["run"]["status"] == "completed"

    def test_list_runs_returns_user_runs(self) -> None:
        user_id = uuid4()
        doc_id = uuid4()
        client = create_test_client(user_id)
        client.post(
            "/api/v1/runs",
            json={
                "document_id": str(doc_id),
                "mode": "endless",
                "question_count": 3,
            },
        )
        client.post(
            "/api/v1/runs",
            json={
                "document_id": str(doc_id),
                "mode": "speed",
                "question_count": 5,
            },
        )
        response = client.get("/api/v1/runs")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2

    def test_create_run_requires_auth(self) -> None:
        app = create_app()
        client = TestClient(app)
        response = client.post(
            "/api/v1/runs",
            json={
                "document_id": str(uuid4()),
                "mode": "endless",
                "question_count": 5,
            },
        )
        assert response.status_code == 401
