"""FastAPI service: POST /ask plus a static HTML front end and a few helper endpoints."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")  # must run before app.config reads the environment

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.concurrency import run_in_threadpool  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from . import config, evaljob, llm  # noqa: E402
from .audit import load_audit  # noqa: E402
from .llm import LLMError  # noqa: E402
from .pipeline import ask  # noqa: E402
from .retriever import Retriever, load_index  # noqa: E402
from .schemas import AskRequest, AskResponse  # noqa: E402

STATIC = ROOT / "static"
TESTS = ROOT / "tests" / "questions.json"
state: dict[str, Retriever] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    r = load_index()
    r.embed_query("warm up the encoder")
    state["retriever"] = r
    evaljob.load_saved()
    yield


app = FastAPI(title="The Rulebook That Argues With Itself", version="1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    """Always answer JSON, so the front end can show the reason instead of a parse error."""
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"[:500]})


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
async def health():
    r = state.get("retriever")
    return {
        "ok": r is not None,
        "sections": len(r.chunks) if r else 0,
        "embedding_model": config.EMBEDDING_MODEL,
        "llm_available": llm.available(),
        "llm_model": (llm.model_chain()[0].id if llm.available() and llm.model_chain() else None),
        "llm_chain": llm.model_status() if llm.available() else {},
        "quota": llm.quota_status(),
        "top_k": config.TOP_K,
        "min_similarity": config.MIN_SIMILARITY,
    }


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(req: AskRequest):
    r = state.get("retriever")
    if r is None:
        raise HTTPException(503, "index not loaded yet")
    try:
        return await run_in_threadpool(ask, req.question, r, req.top_k, req.spread)
    except LLMError as e:
        # 503, not 502: Cloudflare (the tunnel) replaces an origin 502 with its own HTML error
        # page, which hides the reason. A 503 with a JSON body passes through untouched.
        raise HTTPException(503, f"LLM error: {e}") from e


@app.get("/sections")
async def sections():
    r = state.get("retriever")
    if r is None:
        raise HTTPException(503, "index not loaded yet")
    return [{"id": c.id, "doc": c.doc_title, "title": c.title, "parent": c.parent_title,
             "format": c.format, "source": c.source, "words": len(c.text.split())} for c in r.chunks]


@app.get("/questions")
async def questions():
    if not TESTS.exists():
        return {"answerable": [], "conflict": [], "not_covered": []}
    return json.loads(TESTS.read_text(encoding="utf-8"))


class EvalRunRequest(BaseModel):
    workers: int = Field(3, ge=1, le=6)
    spread: bool = True


@app.get("/eval")
async def eval_state():
    """Progress and results of the current or last evaluation run (survives page refreshes)."""
    return evaljob.state()


@app.post("/eval/run")
async def eval_run(req: EvalRunRequest | None = None):
    r = state.get("retriever")
    if r is None:
        raise HTTPException(503, "index not loaded yet")
    req = req or EvalRunRequest()
    return evaljob.start(r, workers=req.workers, spread=req.spread)


@app.post("/eval/cancel")
async def eval_cancel():
    return evaljob.cancel()


@app.get("/audit")
async def audit():
    """Latest corpus-wide contradiction audit (run scripts/audit.py to refresh)."""
    report = load_audit()
    if report is None:
        return {"available": False, "hint": "run: python scripts/audit.py"}
    return {"available": True, **report}
