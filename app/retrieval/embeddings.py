from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL_NAME = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


class EmbeddingModel:
    """
    Thin wrapper around SentenceTransformer.

    Embeddings are normalized so that inner-product search
    in FAISS corresponds to cosine similarity.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:

        self.model_name = model_name

        self.model = SentenceTransformer(
            model_name
        )

    def encode_documents(
        self,
        texts: Sequence[str],
        batch_size: int = 32,
    ) -> np.ndarray:
        """
        Encode corpus documents.
        """

        embeddings = self.model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return np.asarray(
            embeddings,
            dtype=np.float32,
        )

    def encode_query(
        self,
        text: str,
    ) -> np.ndarray:
        """
        Encode one search query.
        """

        embedding = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return np.asarray(
            embedding,
            dtype=np.float32,
        )