from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.verifier import (
    browse_corpus,
    get_corpus_by_number,
    get_corpus_stats,
    load_corpus,
    parse_dataset,
    search_corpus,
    validate_corpus,
    verify_quote,
)

app = FastAPI(title="Thirukkural Reliability Lab", version="1.0.0")


class VerifyRequest(BaseModel):
    quotation: str = Field(default="")
    quote: str | None = None
    claimed_kural_number: int | str | None = None

    @property
    def text(self) -> str:
        return (self.quotation or self.quote or "").strip()


class BatchVerifyItem(BaseModel):
    response_id: str | None = None
    model: str | None = None
    prompt: str | None = None
    quotation: str = ""
    claimed_kural_number: int | str | None = None


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok", "service": "thirukkural-verifier"}


@app.get("/api/corpus/stats")
def corpus_stats() -> dict:
    return get_corpus_stats()


@app.get("/api/corpus/search")
def corpus_search(query: str | None = None, limit: int = 10) -> list[dict]:
    return search_corpus(query, limit=limit)


@app.get("/api/corpus/browse")
def corpus_browse(query: str | None = None, chapter: str | None = None, offset: int = 0, limit: int = 20) -> dict:
    return browse_corpus(query=query, chapter=chapter, offset=offset, limit=limit)


@app.get("/api/corpus/{kural_number}")
def corpus_item(kural_number: int) -> dict:
    item = get_corpus_by_number(kural_number)
    if item is None:
        raise HTTPException(status_code=404, detail="Kural not found")
    return item


@app.post("/api/verify")
def verify_endpoint(payload: VerifyRequest) -> dict:
    quotation = payload.text
    if not quotation:
        return verify_quote("")
    return verify_quote(quotation, claimed_kural_number=payload.claimed_kural_number)


@app.post("/api/batch/verify")
def batch_verify(items: list[BatchVerifyItem]) -> list[dict]:
    results: list[dict] = []
    for item in items:
        result = verify_quote(item.quotation, item.claimed_kural_number)
        results.append({
            "response_id": item.response_id,
            "model": item.model,
            "prompt": item.prompt,
            "quotation": item.quotation,
            "claimed_kural_number": item.claimed_kural_number,
            "result": result,
        })
    return results


@app.get("/api/corpus/sample")
def sample_corpus() -> list[dict]:
    corpus = load_corpus()
    return corpus[:5]


@app.get("/api/validation")
def validation_status() -> dict:
    return validate_corpus()


@app.post("/api/dataset/parse")
def parse_dataset_endpoint() -> dict:
    return parse_dataset()
