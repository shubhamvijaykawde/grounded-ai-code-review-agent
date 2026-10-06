from app.parsing.models import CodeChunk
from app.retrieval.embeddings import (
    EmbeddingModel,
)
from app.retrieval.faiss_store import (
    FAISSChunkStore,
)
from app.retrieval.lexical import (
    TFIDFRetriever,
)
from app.retrieval.models import (
    RetrievalResult,
)


RRF_K = 60


class HybridRetriever:
    """
    Hybrid dense + lexical retriever.

    Dense retrieval:
        SentenceTransformer + FAISS

    Lexical retrieval:
        TF-IDF

    Results are combined using Reciprocal Rank Fusion.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        dense_store: FAISSChunkStore,
        lexical_retriever: TFIDFRetriever,
    ) -> None:

        self.embedding_model = (
            embedding_model
        )

        self.dense_store = dense_store

        self.lexical_retriever = (
            lexical_retriever
        )

    @classmethod
    def build(
        cls,
        chunks: list[CodeChunk],
        model_name: str | None = None,
    ) -> "HybridRetriever":

        if not chunks:
            raise ValueError(
                "Cannot build hybrid retriever with no chunks."
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

        dense_store = (
            FAISSChunkStore.build(
                embeddings=embeddings,
                chunks=chunks,
            )
        )

        print(
            "Building TF-IDF index..."
        )

        lexical_retriever = (
            TFIDFRetriever.build(
                chunks
            )
        )

        return cls(
            embedding_model=embedding_model,
            dense_store=dense_store,
            lexical_retriever=lexical_retriever,
        )

    def _dense_search(
        self,
        query: str,
        top_k: int,
    ) -> list[RetrievalResult]:

        query_embedding = (
            self.embedding_model.encode_query(
                query
            )
        )

        return self.dense_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

    def _rrf(
        self,
        dense_results: list[RetrievalResult],
        lexical_results: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:
        """
        Reciprocal Rank Fusion.

        RRF score:
            1 / (k + rank)

        We use ranks rather than raw dense/TF-IDF scores,
        so the two retrieval systems do not need to have
        comparable score ranges.
        """

        scores: dict[str, float] = {}

        chunks_by_id: dict[
            str,
            CodeChunk,
        ] = {}

        for rank, result in enumerate(
            dense_results,
            start=1,
        ):

            chunk_id = (
                result.chunk.chunk_id
            )

            scores[chunk_id] = (
                scores.get(
                    chunk_id,
                    0.0,
                )
                + 1.0
                / (
                    RRF_K + rank
                )
            )

            chunks_by_id[
                chunk_id
            ] = result.chunk

        for rank, result in enumerate(
            lexical_results,
            start=1,
        ):

            chunk_id = (
                result.chunk.chunk_id
            )

            scores[chunk_id] = (
                scores.get(
                    chunk_id,
                    0.0,
                )
                + 1.0
                / (
                    RRF_K + rank
                )
            )

            chunks_by_id[
                chunk_id
            ] = result.chunk

        ranked_ids = sorted(
            scores,
            key=lambda chunk_id:
                scores[chunk_id],
            reverse=True,
        )[:top_k]

        return [
            RetrievalResult(
                chunk=chunks_by_id[
                    chunk_id
                ],
                score=scores[
                    chunk_id
                ],
                rank=rank,
            )
            for rank, chunk_id in enumerate(
                ranked_ids,
                start=1,
            )
        ]

    def search(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 20,
    ) -> list[RetrievalResult]:

        dense_results = (
            self._dense_search(
                query,
                top_k=candidate_k,
            )
        )

        lexical_results = (
            self.lexical_retriever.search(
                query,
                top_k=candidate_k,
            )
        )

        return self._rrf(
            dense_results=dense_results,
            lexical_results=lexical_results,
            top_k=top_k,
        )