"""
RAG Pipeline — Semantic document search with ChromaDB + sentence-transformers.

Replaces the naive substring search in mock_document_tool.py.
On first startup, documents are embedded and stored in ./chroma_db.
Subsequent startups load the persisted index — no re-embedding needed.
"""
import os
import glob
import logging

logger = logging.getLogger(__name__)

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "documents")

# Lazy imports so the app starts even if chromadb isn't installed yet
_chromadb = None
_st_ef = None


def _get_chromadb():
    global _chromadb
    if _chromadb is None:
        import chromadb
        _chromadb = chromadb
    return _chromadb


def _get_embedding_function(model_name: str = "all-MiniLM-L6-v2"):
    global _st_ef
    if _st_ef is None:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        _st_ef = SentenceTransformerEmbeddingFunction(model_name=model_name)
    return _st_ef


class RAGPipeline:
    """
    Singleton RAG pipeline backed by ChromaDB.
    Usage: rag_pipeline.search("high temperature alarm", top_k=3)
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance.client = None
            cls._instance.collection = None
        return cls._instance

    def initialize(self, chroma_dir: str = "./chroma_db", embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize ChromaDB client and embed documents if needed. Idempotent."""
        if self._initialized:
            return

        try:
            chromadb = _get_chromadb()
            ef = _get_embedding_function(embedding_model)

            self.client = chromadb.PersistentClient(path=chroma_dir)
            self.collection = self.client.get_or_create_collection(
                name="agenticos_documents",
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"},
            )

            # Embed documents only if the collection is empty
            if self.collection.count() == 0:
                logger.info("RAG: Embedding documents on first run (this takes ~10s)...")
                self._embed_documents()
                logger.info(f"RAG: Embedded {self.collection.count()} chunks into ChromaDB.")
            else:
                logger.info(f"RAG: Loaded existing index with {self.collection.count()} chunks.")

            self._initialized = True

        except Exception as e:
            logger.warning(f"RAG pipeline init failed: {e}. Falling back to keyword search.")
            self._initialized = False

    def _embed_documents(self):
        """Load all .md documents, split by section, and embed."""
        ids, documents, metadatas = [], [], []

        for filepath in glob.glob(os.path.join(DOCS_DIR, "*.md")):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Split into sections on markdown horizontal rules
                sections = [s.strip() for s in content.split("---") if len(s.strip()) > 50]

                for i, section in enumerate(sections):
                    doc_id = f"{filename}_s{i}"
                    ids.append(doc_id)
                    documents.append(section)
                    metadatas.append({"source": filename, "section_index": i})

            except Exception as e:
                logger.warning(f"RAG: Failed to load {filename}: {e}")

        if ids:
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def search(self, query: str, top_k: int = 3, source_filter: str | None = None) -> list[dict]:
        """
        Semantic search over embedded documents.

        Args:
            query: Natural language query string.
            top_k: Number of results to return.
            source_filter: Optional filename to restrict results (e.g. 'hvac_sop.md').

        Returns:
            List of dicts with keys: content, source, relevance_score.
        """
        if not self._initialized or self.collection is None:
            return self._keyword_fallback(query, top_k)

        try:
            count = self.collection.count()
            if count == 0:
                return []

            where_filter = {"source": source_filter} if source_filter else None

            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, count),
                where=where_filter if where_filter else None,
            )

            output = []
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i] if results.get("distances") else 0.1
                relevance = round(max(0.0, 1.0 - distance), 3)
                output.append({
                    "content": doc,
                    "source": results["metadatas"][0][i]["source"],
                    "relevance_score": relevance,
                })
            return output

        except Exception as e:
            logger.warning(f"RAG search failed: {e}. Falling back to keyword search.")
            return self._keyword_fallback(query, top_k)

    def _keyword_fallback(self, query: str, top_k: int) -> list[dict]:
        """Graceful fallback: substring search when ChromaDB is unavailable."""
        results = []
        query_lower = query.lower()
        for filepath in glob.glob(os.path.join(DOCS_DIR, "*.md")):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                if query_lower in content.lower():
                    # Extract the most relevant snippet
                    idx = content.lower().find(query_lower)
                    snippet = content[max(0, idx - 100): idx + 500].strip()
                    results.append({
                        "content": snippet,
                        "source": filename,
                        "relevance_score": 0.5,
                    })
            except Exception:
                pass
        return results[:top_k]


# Module-level singleton — imported by mock_document_tool
rag_pipeline = RAGPipeline()
