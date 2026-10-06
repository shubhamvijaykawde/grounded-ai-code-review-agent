from pathlib import Path

from app.analysis.models import Finding
from app.parsing.models import CodeChunk
from app.retrieval.embeddings import (
    EmbeddingModel,
)
from app.retrieval.faiss_store import (
    FAISSChunkStore,
)
from app.retrieval.models import (
    RetrievalResult,
)
from app.retrieval.text import (
    finding_to_query,
)


class CodeRetriever:
    """
    High-level semantic retriever over AST code chunks.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        store: FAISSChunkStore,
    ) -> None:

        self.embedding_model = (
            embedding_model
        )

        self.store = store

    @classmethod
    def build(
        cls,
        chunks: list[CodeChunk],
        model_name: str | None = None,
    ) -> "CodeRetriever":

        if not chunks:
            raise ValueError(
                "Cannot build retriever with no chunks."
            )

        if model_name:
            embedding_model = (
                EmbeddingModel(
                    model_name=model_name
                )
            )
        else:
            embedding_model = (
                EmbeddingModel()
            )

        from app.retrieval.text import (
            chunk_to_embedding_text,
        )

        texts = [
            chunk_to_embedding_text(
                chunk
            )
            for chunk in chunks
        ]

        print(
            f"Encoding {len(texts)} chunks..."
        )

        embeddings = (
            embedding_model.encode_documents(
                texts
            )
        )

        store = (
            FAISSChunkStore.build(
                embeddings=embeddings,
                chunks=chunks,
            )
        )

        return cls(
            embedding_model=embedding_model,
            store=store,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        query_embedding = (
            self.embedding_model.encode_query(
                query
            )
        )

        return self.store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

    def search_finding(
        self,
        finding: Finding,
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        query = finding_to_query(
            finding
        )

        return self.search(
            query,
            top_k=top_k,
        )

    def save(
        self,
        directory: Path,
    ) -> None:

        self.store.save(
            directory
        )