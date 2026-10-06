import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from app.parsing.models import CodeChunk
from app.retrieval.models import RetrievalResult
from app.retrieval.text import (
    chunk_to_embedding_text,
)


class TFIDFRetriever:
    """
    Lexical retrieval over CodeChunk text.

    TF-IDF captures exact terms and identifiers that semantic
    embeddings may overlook.
    """

    def __init__(
        self,
        chunks: list[CodeChunk],
        vectorizer: TfidfVectorizer,
        matrix,
    ) -> None:

        self.chunks = chunks
        self.vectorizer = vectorizer
        self.matrix = matrix

    @classmethod
    def build(
        cls,
        chunks: list[CodeChunk],
    ) -> "TFIDFRetriever":

        if not chunks:
            raise ValueError(
                "Cannot build TF-IDF retriever with no chunks."
            )

        documents = [
            chunk_to_embedding_text(
                chunk
            )
            for chunk in chunks
        ]

        vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=100_000,
        )

        matrix = vectorizer.fit_transform(
            documents
        )

        return cls(
            chunks=chunks,
            vectorizer=vectorizer,
            matrix=matrix,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        if not self.chunks:
            return []

        query_vector = (
            self.vectorizer.transform(
                [query]
            )
        )

        scores = linear_kernel(
            query_vector,
            self.matrix,
        ).flatten()

        top_k = min(
            top_k,
            len(self.chunks),
        )

        # argpartition is faster than sorting the
        # entire corpus when only top-k is needed.
        candidate_indices = np.argpartition(
            -scores,
            top_k - 1,
        )[:top_k]

        # Sort those candidates by actual score.
        candidate_indices = candidate_indices[
            np.argsort(
                -scores[candidate_indices]
            )
        ]

        results = []

        for rank, index in enumerate(
            candidate_indices,
            start=1,
        ):

            results.append(
                RetrievalResult(
                    chunk=self.chunks[
                        int(index)
                    ],
                    score=float(
                        scores[index]
                    ),
                    rank=rank,
                )
            )

        return results