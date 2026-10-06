from dataclasses import dataclass

from app.parsing.models import CodeChunk


@dataclass
class RetrievalResult:
    """
    One semantic retrieval result.
    """

    chunk: CodeChunk

    score: float

    rank: int