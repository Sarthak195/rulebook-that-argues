"""Hybrid retrieval: dense cosine similarity (bge-small) fused with BM25 by reciprocal rank.

Why hybrid: regulations are full of exact tokens that embeddings blur ("65 per cent", "Rs. 800",
"hall ticket"). BM25 keeps those sharp; the dense model handles paraphrase ("can I skip the exam
for a wedding" vs "absence from examination"). The similarity score shown to the user is always
the dense cosine, because that is the number a reader can interpret.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import config
from .chunking import Chunk, dump, load, load_corpus

TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass
class Hit:
    chunk: Chunk
    score: float        # dense cosine similarity, in [-1, 1]
    bm25: float
    dense_rank: int
    bm25_rank: int
    fused: float


class Retriever:
    def __init__(self, chunks: list[Chunk], embeddings: np.ndarray, model_name: str = config.EMBEDDING_MODEL):
        from rank_bm25 import BM25Okapi

        self.chunks = chunks
        self.emb = embeddings.astype(np.float32)
        self.model_name = model_name
        self._model = None
        self.bm25 = BM25Okapi([tokenize(c.embed_text) for c in chunks])
        self.by_id = {c.id: c for c in chunks}

    # -- model ---------------------------------------------------------------
    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_query(self, query: str) -> np.ndarray:
        return self.model.encode(config.QUERY_PREFIX + query, normalize_embeddings=True).astype(np.float32)

    # -- search --------------------------------------------------------------
    def search(self, query: str, k: int = config.TOP_K, pool: int = 12, rrf_k: int = 60) -> list[Hit]:
        q = self.embed_query(query)
        dense = self.emb @ q
        bm25 = np.asarray(self.bm25.get_scores(tokenize(query)), dtype=np.float32)

        dense_order = np.argsort(-dense)[:pool]
        bm25_order = np.argsort(-bm25)[:pool]
        dense_rank = {int(i): r for r, i in enumerate(dense_order)}
        bm25_rank = {int(i): r for r, i in enumerate(bm25_order)}

        fused: dict[int, float] = {}
        for i, r in dense_rank.items():
            fused[i] = fused.get(i, 0.0) + 1.0 / (rrf_k + r)
        for i, r in bm25_rank.items():
            # BM25 with a zero score carries no evidence; do not let it vote.
            if bm25[i] > 0:
                fused[i] = fused.get(i, 0.0) + 1.0 / (rrf_k + r)

        top = sorted(fused.items(), key=lambda kv: (-kv[1], -dense[kv[0]]))[:k]
        return [
            Hit(chunk=self.chunks[i], score=float(dense[i]), bm25=float(bm25[i]),
                dense_rank=dense_rank.get(i, -1), bm25_rank=bm25_rank.get(i, -1), fused=f)
            for i, f in top
        ]

    def dense_only(self, query: str, k: int = 1) -> list[Hit]:
        q = self.embed_query(query)
        dense = self.emb @ q
        order = np.argsort(-dense)[:k]
        return [Hit(self.chunks[int(i)], float(dense[i]), 0.0, r, -1, 0.0) for r, i in enumerate(order)]


# -- index build / load ---------------------------------------------------------
def build_index(corpus_dir: Path = config.CORPUS_DIR, index_dir: Path = config.INDEX_DIR,
                model_name: str = config.EMBEDDING_MODEL, log=print) -> Retriever:
    from sentence_transformers import SentenceTransformer

    t0 = time.time()
    chunks = load_corpus(corpus_dir)
    log(f"parsed {len(chunks)} sections from {corpus_dir}")
    model = SentenceTransformer(model_name)
    emb = model.encode([c.embed_text for c in chunks], normalize_embeddings=True, batch_size=32,
                       show_progress_bar=False)
    index_dir.mkdir(parents=True, exist_ok=True)
    dump(chunks, index_dir / "chunks.json")
    np.save(index_dir / "embeddings.npy", emb.astype(np.float32))
    (index_dir / "meta.txt").write_text(f"{model_name}\n{len(chunks)}\n", encoding="utf-8")
    log(f"embedded with {model_name} -> {index_dir} in {time.time() - t0:.1f}s")
    r = Retriever(chunks, emb, model_name)
    r._model = model
    return r


def load_index(index_dir: Path = config.INDEX_DIR, model_name: str = config.EMBEDDING_MODEL, log=print) -> Retriever:
    chunks_path, emb_path, meta_path = index_dir / "chunks.json", index_dir / "embeddings.npy", index_dir / "meta.txt"
    if chunks_path.exists() and emb_path.exists() and meta_path.exists():
        stored_model = meta_path.read_text(encoding="utf-8").splitlines()[0].strip()
        if stored_model == model_name:
            chunks = load(chunks_path)
            emb = np.load(emb_path)
            if len(chunks) == emb.shape[0]:
                log(f"loaded index: {len(chunks)} sections, model {model_name}")
                return Retriever(chunks, emb, model_name)
    log("index missing or stale; rebuilding")
    return build_index(index_dir=index_dir, model_name=model_name, log=log)
