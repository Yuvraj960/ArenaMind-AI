from typing import Optional
from fastapi import APIRouter, Query

from app.models.schemas import KnowledgeSearchResults, KnowledgeSearchResult
from app.rag.retriever import get_knowledge_retriever

router = APIRouter()


@router.get("/search", response_model=KnowledgeSearchResults)
async def search_knowledge(
    query: str = Query(..., description="Natural-language query"),
    role: str = Query("fan", description="Stakeholder role for access scoping"),
    category: Optional[str] = None,
    top_k: int = Query(5, ge=1, le=20),
):
    """Search the shared RAG knowledge base, scoped to the caller's role."""
    retriever = await get_knowledge_retriever()
    docs = await retriever.search(query, role=role, category=category, top_k=top_k)
    results = [
        KnowledgeSearchResult(
            content=d.page_content,
            score=getattr(d, "score", 1.0),
            metadata=d.metadata,
        )
        for d in docs
    ]
    return KnowledgeSearchResults(results=results, query=query)


@router.get("/ingest")
async def ingest_knowledge_base():
    """Ingest the knowledge_base/ directory into Qdrant. Idempotent."""
    from app.rag.retriever import KnowledgeIngestor
    ingester = KnowledgeIngestor()
    await ingester.ingest_knowledge_base()
    return {"success": True, "message": "Ingestion complete"}