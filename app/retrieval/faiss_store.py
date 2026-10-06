import json
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np

from app.parsing.models import CodeChunk
from app.retrieval.models import RetrievalResult


class FAISSChunkStore:
    """
    FAISS vector store for CodeChunk objects.

    FAISS stores vectors.
    The actual CodeChunk metadata is stored separately in JSON.
    """

    def __init__(
        self,
        index: faiss.Index,
        chunks: list[CodeChunk],
    ) -> None:

        self.index = index
        self.chunks = chunks

    @classmethod
    def build(
        cls,
        embeddings: np.ndarray,
        chunks: list[CodeChunk],
    ) -> "FAISSChunkStore":
        """
        Build an exact inner-product FAISS index.
        """

        if len(chunks) == 0:
            raise ValueError(
                "Cannot build FAISS index with no chunks."
            )

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Number of embeddings must equal "
                "number of chunks."
            )

        vectors = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        dimension = vectors.shape[1]

        index = faiss.IndexFlatIP(
            dimension
        )

        index.add(
            vectors
        )

        return cls(
            index=index,
            chunks=chunks,
        )

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """
        Search the vector index.
        """

        if self.index.ntotal == 0:
            return []

        top_k = min(
            top_k,
            self.index.ntotal,
        )

        query = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        if query.ndim == 1:
            query = query.reshape(
                1,
                -1,
            )

        scores, indices = (
            self.index.search(
                query,
                top_k,
            )
        )

        results: list[
            RetrievalResult
        ] = []

        for rank, (
            score,
            index,
        ) in enumerate(
            zip(
                scores[0],
                indices[0],
            ),
            start=1,
        ):

            if index < 0:
                continue

            results.append(
                RetrievalResult(
                    chunk=self.chunks[
                        int(index)
                    ],
                    score=float(score),
                    rank=rank,
                )
            )

        return results

    def save(
        self,
        directory: Path,
    ) -> None:
        """
        Save FAISS index and chunk metadata.
        """

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss_path = (
            directory
            / "code_chunks.faiss"
        )

        metadata_path = (
            directory
            / "code_chunks.json"
        )

        faiss.write_index(
            self.index,
            str(faiss_path),
        )

        metadata_path.write_text(
            json.dumps(
                [
                    asdict(chunk)
                    for chunk
                    in self.chunks
                ],
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(
        cls,
        directory: Path,
    ) -> "FAISSChunkStore":
        """
        Load FAISS index and associated chunks.
        """

        faiss_path = (
            directory
            / "code_chunks.faiss"
        )

        metadata_path = (
            directory
            / "code_chunks.json"
        )

        if not faiss_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {faiss_path}"
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Chunk metadata not found: {metadata_path}"
            )

        index = faiss.read_index(
            str(faiss_path)
        )

        raw_chunks = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        chunks = [
            CodeChunk(
                **item
            )
            for item in raw_chunks
        ]

        if index.ntotal != len(chunks):
            raise ValueError(
                "FAISS index size does not match "
                "chunk metadata."
            )

        return cls(
            index=index,
            chunks=chunks,
        )