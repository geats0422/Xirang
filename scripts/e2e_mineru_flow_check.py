from __future__ import annotations

import json
import time
import importlib
import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx


BASE_URL = "http://127.0.0.1:8000"
PDF_PATH = Path("D:/project/Xirang/tmp_uploads/13、-AI行业落地案例补充知识.pdf")
READY_TIMEOUT_SECONDS = int(os.getenv("E2E_READY_TIMEOUT_SECONDS", "2400"))


@dataclass
class E2EResult:
    user_email: str
    document_id: str
    job_id: str
    document_status: str
    path_option_count: int
    selected_path_id: str
    run_id: str
    generated_question_count: int


def _raise_for_http(response: httpx.Response, context: str) -> None:
    if response.is_success:
        return

    message = (
        f"{context} failed: status={response.status_code}, body={response.text[:1200]}"
    )
    raise RuntimeError(message)


def _register_and_get_token(session: httpx.Client) -> tuple[str, str, str]:
    seed = uuid4().hex[:10]
    email = f"mineru-e2e-{seed}@example.com"
    username = f"mineru_e2e_{seed}"
    password = "Passw0rd!Passw0rd!"

    register_response = session.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
        timeout=30,
    )
    _raise_for_http(register_response, "register")

    body = register_response.json()
    token = body.get("tokens", {}).get("access_token")
    if not token:
        raise RuntimeError(
            f"register response missing access token: {register_response.text[:500]}"
        )

    return email, password, token


def _login_and_get_token(session: httpx.Client, identity: str, password: str) -> str:
    login_response = session.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"identity": identity, "password": password},
        timeout=30,
    )
    _raise_for_http(login_response, "login")
    body = login_response.json()
    token = body.get("tokens", {}).get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError(
            f"login response missing access token: {login_response.text[:500]}"
        )
    return token


def _upload_document(session: httpx.Client, token: str) -> tuple[str, str]:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    headers = {"Authorization": f"Bearer {token}"}
    with PDF_PATH.open("rb") as fh:
        upload_response = session.post(
            f"{BASE_URL}/api/v1/documents/upload",
            headers=headers,
            data={"title": "MinerU E2E PDF Test", "format": "pdf"},
            files={"file": (PDF_PATH.name, fh, "application/pdf")},
            timeout=120,
        )
    _raise_for_http(upload_response, "upload document")

    body = upload_response.json()
    document_id = body.get("document", {}).get("id")
    job_id = body.get("job", {}).get("id")
    if not document_id or not job_id:
        raise RuntimeError(
            f"upload response missing document/job id: {upload_response.text[:800]}"
        )

    return document_id, job_id


def _poll_ready(
    session: httpx.Client, token: str, document_id: str, job_id: str
) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + READY_TIMEOUT_SECONDS
    last_job: dict[str, Any] = {}
    last_doc: dict[str, Any] = {}

    while time.time() < deadline:
        job_response = session.get(
            f"{BASE_URL}/api/v1/documents/jobs/{job_id}",
            headers=headers,
            timeout=30,
        )
        _raise_for_http(job_response, "poll job")
        last_job = job_response.json()

        document_response = session.get(
            f"{BASE_URL}/api/v1/documents/{document_id}",
            headers=headers,
            timeout=30,
        )
        _raise_for_http(document_response, "poll document")
        last_doc = document_response.json()

        job_status = str(last_job.get("status", "")).lower()
        doc_status = str(last_doc.get("status", "")).lower()

        if job_status == "failed" or doc_status == "failed":
            raise RuntimeError(
                "ingestion failed: "
                f"job={json.dumps(last_job, ensure_ascii=False)} "
                f"document={json.dumps(last_doc, ensure_ascii=False)}"
            )

        if job_status == "completed" and doc_status == "ready":
            return doc_status

        time.sleep(2)

    raise TimeoutError(
        "timed out waiting for document ready; "
        f"last_job={json.dumps(last_job, ensure_ascii=False)} "
        f"last_doc={json.dumps(last_doc, ensure_ascii=False)}"
    )


def _pump_worker_until_job_finished(
    *,
    target_job_id: str,
    queue_name: str = "default",
    max_seconds: int = 2400,
) -> None:
    async def _run() -> None:
        session_module = importlib.import_module("app.db.session")
        repo_module = importlib.import_module("app.repositories.document_repository")
        job_runner_module = importlib.import_module("app.workers.job_runner")
        worker_main_module = importlib.import_module("app.workers.main")

        get_session_factory = getattr(session_module, "get_session_factory")
        document_repository_cls = getattr(repo_module, "DocumentRepository")
        job_runner_cls = getattr(job_runner_module, "JobRunner")
        worker_repo_cls = getattr(worker_main_module, "WorkerJobRepository")
        build_job_registry = getattr(worker_main_module, "build_job_registry")

        registry = build_job_registry()
        session_factory = get_session_factory()
        deadline = time.time() + max_seconds
        async with session_factory() as session:
            repo = document_repository_cls(session)
            worker_repo = worker_repo_cls(repo)
            runner = job_runner_cls(repository=worker_repo, registry=registry)

            while time.time() < deadline:
                current_job = await repo.get_job_by_id(target_job_id)
                if current_job is not None:
                    status = str(current_job.status).lower()
                    if status in {"completed", "failed"}:
                        return

                processed = await runner.run_one(queue_name=queue_name)
                if not processed:
                    await asyncio.sleep(0.5)

            raise TimeoutError(
                f"worker did not finish target job in time: {target_job_id}"
            )

    import asyncio

    asyncio.run(_run())


def _fetch_path_options(
    session: httpx.Client,
    token: str,
    document_id: str,
    mode: str = "endless",
) -> tuple[list[dict[str, Any]], str]:
    headers = {"Authorization": f"Bearer {token}"}
    response = session.get(
        f"{BASE_URL}/api/v1/runs/path-options",
        headers=headers,
        params={"mode": mode, "document_id": document_id},
        timeout=30,
    )
    _raise_for_http(response, "fetch path options")

    body = response.json()
    options = body.get("options") if isinstance(body, dict) else None
    if not isinstance(options, list):
        raise RuntimeError(f"path options response malformed: {response.text[:800]}")

    if not options:
        raise RuntimeError(
            "path options is empty; required flow is document -> path options -> run/questions"
        )

    first = options[0]
    if not isinstance(first, dict):
        raise RuntimeError("first path option is not an object")

    value = first.get("path_id")
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("first path option missing path_id")

    return options, value


def _create_run(
    session: httpx.Client,
    token: str,
    document_id: str,
    path_id: str,
) -> tuple[str, int]:
    headers = {"Authorization": f"Bearer {token}"}
    payload: dict[str, Any] = {
        "document_id": document_id,
        "mode": "endless",
        "question_count": 5,
        "path_id": path_id,
    }

    response = session.post(
        f"{BASE_URL}/api/v1/runs",
        headers=headers,
        json=payload,
        timeout=60,
    )
    _raise_for_http(response, "create run")

    body = response.json()
    run_id = body.get("run_id")
    questions = body.get("questions")
    if not isinstance(run_id, str):
        raise RuntimeError(f"create run response missing run_id: {response.text[:800]}")
    if not isinstance(questions, list):
        raise RuntimeError(
            f"create run response missing questions list: {response.text[:800]}"
        )

    return run_id, len(questions)


def main() -> None:
    health = httpx.get(f"{BASE_URL}/health", timeout=10)
    _raise_for_http(health, "backend health")

    session = httpx.Client(timeout=120)
    user_email, password, token = _register_and_get_token(session)
    document_id, job_id = _upload_document(session, token)
    _pump_worker_until_job_finished(target_job_id=job_id, queue_name="default")
    token = _login_and_get_token(session, user_email, password)
    document_status = _poll_ready(session, token, document_id, job_id)
    options, path_id = _fetch_path_options(session, token, document_id)
    run_id, question_count = _create_run(session, token, document_id, path_id)

    result = E2EResult(
        user_email=user_email,
        document_id=document_id,
        job_id=job_id,
        document_status=document_status,
        path_option_count=len(options),
        selected_path_id=path_id,
        run_id=run_id,
        generated_question_count=question_count,
    )
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
