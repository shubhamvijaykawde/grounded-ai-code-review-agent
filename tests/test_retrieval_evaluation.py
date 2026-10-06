from app.parsing.models import CodeChunk
from app.retrieval.evaluation import (
    CaseResult,
    recall_at_k,
    mean_reciprocal_rank,
)
from app.retrieval.models import RetrievalResult


def make_result(
    expected: str,
    rank: int | None,
) -> CaseResult:

    ids = []

    if rank is not None:

        for i in range(1, 6):

            if i == rank:
                ids.append(
                    expected
                )
            else:
                ids.append(
                    f"other-{i}"
                )

    return CaseResult(
        expected_chunk_id=expected,
        retrieved_chunk_ids=ids,
        rank=rank,
        top_score=0.9,
    )


def test_recall_at_1():

    results = [
        make_result("a", 1),
        make_result("b", 2),
        make_result("c", None),
    ]

    assert (
        recall_at_k(results, 1)
        == 1 / 3
    )


def test_recall_at_3():

    results = [
        make_result("a", 1),
        make_result("b", 2),
        make_result("c", 3),
        make_result("d", 4),
    ]

    assert (
        recall_at_k(results, 3)
        == 3 / 4
    )


def test_recall_at_5():

    results = [
        make_result("a", 1),
        make_result("b", 5),
        make_result("c", None),
    ]

    assert (
        recall_at_k(results, 5)
        == 2 / 3
    )


def test_mrr():

    results = [
        make_result("a", 1),
        make_result("b", 2),
        make_result("c", 4),
        make_result("d", None),
    ]

    expected = (
        1
        + 1 / 2
        + 1 / 4
    ) / 4

    assert (
        mean_reciprocal_rank(results)
        == expected
    )


def test_empty_results():

    assert (
        recall_at_k([], 5)
        == 0.0
    )

    assert (
        mean_reciprocal_rank([])
        == 0.0
    )