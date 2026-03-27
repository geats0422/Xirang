from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Mock PageIndex", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/documents/{document_id}/index")
async def index_document(document_id: str, payload: dict[str, object]) -> dict[str, str]:
    _ = payload
    return {"status": "indexed", "document_id": document_id}


@app.post("/documents/{document_id}/search")
async def search_document(
    document_id: str, payload: dict[str, object]
) -> dict[str, list[dict[str, object]]]:
    _ = document_id
    _ = payload
    return {"results": []}


@app.post("/documents/{document_id}/ask")
async def ask_document(document_id: str, payload: dict[str, object]) -> dict[str, object]:
    question = str(payload.get("question", ""))
    return {
        "answer": f"mock-answer: {question}",
        "source_chunks": [],
        "confidence": 0.9,
        "document_id": document_id,
    }


@app.get("/documents/{document_id}/recommendations/{user_id}")
async def recommendations(document_id: str, user_id: str) -> dict[str, list[dict[str, str]]]:
    _ = document_id
    _ = user_id
    return {
        "weak_chapters": [],
        "suggested_questions": [],
    }


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str) -> dict[str, str]:
    return {"status": "deleted", "document_id": document_id}
