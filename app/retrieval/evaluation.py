from dataclasses import dataclass
from typing import Sequence

from app.analysis.models import Finding
from app.retrieval.models import RetrievalResult
from app.retrieval.text import finding_to_semantic_query


@dataclass
class RetrievalCase:
    """
    One retrieval benchmark case.
    """

    finding: Finding

    expected_chunk_id: str

    query: str


@dataclass
class CaseResult:
    """
    Result for one retrieval benchmark case.
    """

    expected_chunk_id: str

    retrieved_chunk_ids: list[str]

    rank: int | None

    top_score: float | None


def build_case(
    finding: Finding,
) -> RetrievalCase | None:
    """
    Build a benchmark case from an enriched Finding.

    A finding without chunk_id cannot have an exact AST ground truth.
    """

    if finding.chunk_id is None:
        return None

    return RetrievalCase(
        finding=finding,
        expected_chunk_id=finding.chunk_id,
        query=finding_to_semantic_query(
            finding
        ),
    )


def evaluate_case(
    case: RetrievalCase,
    results: Sequence[RetrievalResult],
) -> CaseResult:
    """
    Evaluate whether the expected chunk appears in retrieval results.
    """

    retrieved_ids = [
        result.chunk.chunk_id
        for result in results
    ]

    rank = None

    for index, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if chunk_id == case.expected_chunk_id:
            rank = index
            break

    top_score = (
        results[0].score
        if results
        else None
    )

    return CaseResult(
        expected_chunk_id=(
            case.expected_chunk_id
        ),
        retrieved_chunk_ids=retrieved_ids,
        rank=rank,
        top_score=top_score,
    )


def recall_at_k(
    case_results: Sequence[CaseResult],
    k: int,
) -> float:
    """
    Recall@K for single-ground-truth retrieval.

    A case counts as successful when the expected chunk appears
    anywhere in the top K results.
    """

    if not case_results:
        return 0.0

    hits = sum(
        1
        for result in case_results
        if result.rank is not None
        and result.rank <= k
    )

    return hits / len(case_results)


def mean_reciprocal_rank(
    case_results: Sequence[CaseResult],
) -> float:
    """
    Mean Reciprocal Rank.

    Cases not retrieved receive reciprocal rank 0.
    """

    if not case_results:
        return 0.0

    total = 0.0

    for result in case_results:

        if result.rank is not None:
            total += 1.0 / result.rank

    return total / len(case_results)


def evaluate_retrieval(
    retriever,
    cases: Sequence[RetrievalCase],
    top_k: int = 5,
) -> tuple[list[CaseResult], dict[str, float]]:

    results: list[CaseResult] = []

    for case in cases:

        retrieved = retriever.search(
            case.query,
            top_k=top_k,
        )

        results.append(
            evaluate_case(
                case,
                retrieved,
            )
        )

    metrics = {
        "recall_at_1": recall_at_k(
            results,
            1,
        ),
        "recall_at_3": recall_at_k(
            results,
            3,
        ),
        "recall_at_5": recall_at_k(
            results,
            5,
        ),
        "mrr": mean_reciprocal_rank(
            results
        ),
    }

    return results, metrics