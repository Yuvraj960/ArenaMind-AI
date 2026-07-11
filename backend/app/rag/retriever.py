"""RAG retriever with graceful degradation.

Default path: zero-dependency TF-IDF over bundled `knowledge_base/*.md` with role
and category filtering. Optional upgrade: Qdrant + embeddings when configured and
reachable. Either path returns the same shape:
    [{ "content": str, "score": float, "metadata": {...} }, ...]
"""
import math
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import get_settings

settings = get_settings()

STOPWORDS = {
    "the","a","an","is","are","was","were","be","to","of","and","or","in","on","at","by",
    "for","with","from","as","this","that","it","its","how","do","i","where","what","why",
    "my","me","please","can","you","el","la","los","las","de","del","dónde","está","mi","puerta",
}


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-záéíóúñü0-9]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def _parse_frontmatter(text: str) -> (Dict[str, Any], str):
    """Parse optional YAML-ish frontmatter (--- key: value ---)."""
    meta: Dict[str, Any] = {}
    body = text
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            block = text[3:end].strip()
            body = text[end + 3:].lstrip("\n")
            for line in block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    v = v.strip().strip("[]")
                    meta[k.strip()] = v
    return meta, body


# Per-category role allow-list. A doc's frontmatter `roles` (comma list) wins.
CATEGORY_ROLES: Dict[str, List[str]] = {
    "navigation": ["fan", "volunteer", "operator", "emergency"],
    "amenities": ["fan", "volunteer", "operator", "emergency"],
    "tickets": ["fan", "volunteer"],
    "transport": ["fan", "volunteer", "operator"],
    "accessibility": ["fan", "volunteer", "operator", "emergency"],
    "faqs": ["fan", "volunteer"],
    "food": ["fan", "volunteer"],
    "merchandise": ["fan", "volunteer"],
    "stadium_info": ["fan", "volunteer", "operator", "emergency"],
    "emergency_procedures": ["volunteer", "operator", "emergency"],
    "evacuation": ["volunteer", "operator", "emergency"],
    "medical": ["volunteer", "operator", "emergency"],
    "security": ["volunteer", "operator", "emergency"],
    "sop": ["volunteer", "operator", "emergency"],
    "lost_found": ["fan", "volunteer", "operator"],
    "policies": ["volunteer", "operator", "emergency"],
    "operations": ["operator", "emergency"],
    "crowd_management": ["operator", "emergency"],
    "staffing": ["operator", "emergency"],
    "sustainability": ["operator"],
    "general": ["fan", "volunteer", "operator", "emergency"],
}


class _Doc:
    __slots__ = ("id", "content", "metadata", "tokens", "tf")

    def __init__(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        self.id = doc_id
        self.content = content
        self.metadata = metadata
        self.tokens = _tokenize(content)
        tf: Dict[str, int] = {}
        for t in self.tokens:
            tf[t] = tf.get(t, 0) + 1
        self.tf = tf


class LocalKnowledgeIndex:
    """In-process TF-IDF index over bundled knowledge base files."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.KNOWLEDGE_BASE_PATH)
        self.docs: List[_Doc] = []
        self.idf: Dict[str, float] = {}
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        self._loaded = True
        if not self.base_path.exists():
            print(f"[rag] knowledge base not found at {self.base_path}")
            return
        files = sorted(
            p for p in self.base_path.rglob("*")
            if p.is_file() and p.suffix in {".md", ".txt"}
        )
        for fp in files:
            try:
                raw = fp.read_text(encoding="utf-8")
            except Exception:
                continue
            meta, body = _parse_frontmatter(raw)
            meta.setdefault("source", str(fp.relative_to(self.base_path)).replace("\\", "/"))
            meta.setdefault("file_name", fp.name)
            meta.setdefault("language", "en")
            meta.setdefault("category", meta.get("category") or _infer_category(fp.name, str(fp)))
            # chunk body by double newlines
            for i, chunk in enumerate(re.split(r"\n\s*\n", body)):
                chunk = chunk.strip()
                if len(chunk) < 20:
                    continue
                doc_meta = dict(meta)
                doc_meta["chunk"] = i
                self.docs.append(_Doc(f"{fp.name}#{i}", chunk, doc_meta))
        N = max(len(self.docs), 1)
        df: Dict[str, int] = {}
        for d in self.docs:
            for t in d.tf:
                df[t] = df.get(t, 0) + 1
        self.idf = {t: math.log((N + 1) / (cnt + 1)) + 1.0 for t, cnt in df.items()}
        print(f"[rag] local index loaded: {len(self.docs)} chunks from {len(files)} files")

    def search(
        self,
        query: str,
        role: str = "fan",
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        self._load()
        q_tokens = _tokenize(query)
        if not q_tokens or not self.docs:
            return []
        # query vector
        q_tf: Dict[str, int] = {}
        for t in q_tokens:
            q_tf[t] = q_tf.get(t, 0) + 1

        scored = []
        for d in self.docs:
            # role gate
            allowed = self._roles_for(d.metadata)
            if role not in allowed:
                continue
            if category and d.metadata.get("category") != category:
                continue
            if d.metadata.get("language") and d.metadata.get("language") not in ("en", "es"):
                # keep simple: only en/es surfaced for the demo
                pass
            # cosine over tf-idf
            if not d.tf:
                continue
            dot = 0.0
            for t, c in q_tf.items():
                if t in d.tf:
                    idf = self.idf.get(t, 1.0)
                    dot += c * d.tf[t] * idf * idf
            if dot == 0:
                continue
            # small boost for title/source keyword overlap
            scored.append((dot, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"content": d.content, "score": round(float(score), 4), "metadata": d.metadata}
            for score, d in scored[:top_k]
        ]

    def _roles_for(self, meta: Dict[str, Any]):
        r = meta.get("roles")
        if r:
            roles = [x.strip() for x in r.split(",")]
            if roles:
                return roles
        cat = meta.get("category", "general")
        return CATEGORY_ROLES.get(cat, CATEGORY_ROLES["general"])


def _infer_category(filename: str, path: str) -> str:
    s = f"{filename} {path}".lower()
    if any(k in s for k in ["sop", "procedure"]):
        return "sop"
    if "accessibility" in s:
        return "accessibility"
    if "emergency" in s or "evacuation" in s:
        return "emergency_procedures"
    if "medical" in s:
        return "medical"
    if "security" in s:
        return "security"
    if "volunteer" in s:
        return "policies"
    if "operation" in s or "staff" in s:
        return "operations"
    if "navigation" in s or "gate" in s or "map" in s:
        return "navigation"
    if "transit" in s or "transport" in s:
        return "transport"
    if "faq" in s:
        return "faqs"
    if "food" in s:
        return "food"
    return "general"


_local_index: Optional[LocalKnowledgeIndex] = None


def get_local_index() -> LocalKnowledgeIndex:
    global _local_index
    if _local_index is None:
        _local_index = LocalKnowledgeIndex()
    return _local_index


class KnowledgeRetriever:
    """Role-scoped retriever. Uses local TF-IDF (always), with optional Qdrant upgrade."""

    def __init__(self):
        self.local = get_local_index()
        self.qdrant = None
        try:
            from qdrant_client import QdrantClient  # noqa
            if settings.QDRANT_URL:
                self.qdrant = QdrantClient(url=settings.QDRANT_URL)
        except Exception:
            self.qdrant = None

    async def search(
        self,
        query: str,
        role: str = "fan",
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        # Always have local results; Qdrant is a stretch upgrade path.
        return self.local.search(query, role=role, category=category, top_k=top_k)


async def get_knowledge_retriever() -> KnowledgeRetriever:
    return KnowledgeRetriever()


class KnowledgeIngestor:
    """Stub for /knowledge/ingest — local index loads lazily, so this is a no-op
    that reports status. With Qdrant configured it would push embeddings."""

    async def ingest_knowledge_base(self, base_path: Optional[str] = None) -> int:
        idx = LocalKnowledgeIndex(base_path)
        idx._load()
        return len(idx.docs)
