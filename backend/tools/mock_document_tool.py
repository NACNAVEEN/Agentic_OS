"""Mock Document Tools — RAG-powered document retrieval.

Uses the ChromaDB RAG pipeline for semantic search.
Falls back gracefully to keyword search if ChromaDB is unavailable.

New: parameters_schema, module-level cache, real semantic search.
"""
import os
import glob
from typing import Any
from tools.base_tool import BaseTool, _CACHE
from rag.pipeline import rag_pipeline

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "documents")


def _load_documents() -> list[dict]:
    """Load raw documents with caching (for direct text access)."""
    if "documents" not in _CACHE:
        docs = []
        for filepath in glob.glob(os.path.join(DOCS_DIR, "*.md")):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            filename = os.path.basename(filepath)
            docs.append({
                "filename": filename,
                "title": filename.replace("_", " ").replace(".md", "").title(),
                "content": content,
                "path": filepath,
            })
        _CACHE["documents"] = docs
    return _CACHE["documents"]


class MockSearchDocuments(BaseTool):
    """Semantic document search using ChromaDB RAG pipeline."""

    @property
    def name(self) -> str:
        return "search_documents"

    @property
    def description(self) -> str:
        return (
            "Search through technical documents, manuals, and guides using semantic search. "
            "Input: query (string)"
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query",
                    "default": "",
                }
            },
            "required": ["query"],
        }

    def _execute(self, query: str = "", **kwargs) -> Any:
        # Use semantic RAG search
        results = rag_pipeline.search(query, top_k=3)

        if results:
            return {
                "query": query,
                "search_method": "semantic",
                "results": [
                    {
                        "document": r["source"].replace("_", " ").replace(".md", "").title(),
                        "filename": r["source"],
                        "relevantSection": r["content"][:800],
                        "relevanceScore": r["relevance_score"],
                    }
                    for r in results
                ],
                "totalMatches": len(results),
            }

        return {"query": query, "results": [], "totalMatches": 0}


class MockRetrieveSOP(BaseTool):
    """Retrieve Standard Operating Procedures using semantic search."""

    @property
    def name(self) -> str:
        return "retrieve_sop"

    @property
    def description(self) -> str:
        return (
            "Retrieve relevant Standard Operating Procedures for a given topic or issue. "
            "Input: topic (string, e.g. 'high temperature', 'chiller pressure', 'VAV troubleshooting')"
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic or issue to search for SOPs",
                    "default": "",
                }
            },
            "required": ["topic"],
        }

    def _execute(self, topic: str = "", **kwargs) -> Any:
        # Search specifically in SOP and procedure documents
        sop_results = rag_pipeline.search(topic, top_k=3, source_filter="hvac_sop.md")

        # Also search general documents
        general_results = rag_pipeline.search(topic, top_k=2)

        # Merge, deduplicate, sort by relevance
        seen = set()
        all_results = []
        for r in sop_results + general_results:
            key = r["content"][:100]
            if key not in seen:
                seen.add(key)
                all_results.append(r)

        all_results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "topic": topic,
            "search_method": "semantic",
            "procedures": [
                {
                    "document": r["source"].replace("_", " ").replace(".md", "").title(),
                    "content": r["content"][:1500],
                    "source": r["source"],
                    "relevanceScore": r["relevance_score"],
                }
                for r in all_results[:5]
            ],
            "totalFound": len(all_results),
        }
