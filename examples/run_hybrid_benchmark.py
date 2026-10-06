import json
from pathlib import Path

from app.analysis.aggregator import (
    analyze_repository,
)
from app.ingestion.github import (
    ingest_repository,
)
from app.parsing.matcher import (
    attach_chunk_references,
)
from app.parsing.python_ast import (
    parse_repository,
)
from app.retrieval.evaluation import (
    build_case,
    evaluate_retrieval,
)
from app.retrieval.hybrid import (
    HybridRetriever,
)

from app.parsing.scope import (
    classify_chunk_scope,
)


REPOSITORY_URL = (
    "https://github.com/pallets/flask"
)

BENCHMARK_PATH = (
    Path("examples")
    / "retrieval_benchmark.json"
)

RESULT_PATH = (
    Path("examples")
    / "hybrid_benchmark_results.json"
)


def main():

    print(
        "=== LOADING BENCHMARK ==="
    )

    benchmark = json.loads(
        BENCHMARK_PATH.read_text(
            encoding="utf-8"
        )
    )

    expected_ids = {
        case["expected_chunk_id"]
        for case in benchmark["cases"]
    }

    print(
        f"Benchmark cases: "
        f"{len(expected_ids)}"
    )

    print(
        "\n=== INGESTION ==="
    )

    repository = ingest_repository(
        REPOSITORY_URL
    )

    print(
        "\n=== STATIC ANALYSIS ==="
    )

    report = analyze_repository(
        repository
    )

    print(
        "\n=== AST ==="
    )

    ast_result = parse_repository(
        repository
    )

    enriched_findings = (
        attach_chunk_references(
            report.findings,
            ast_result.chunks,
        )
    )

    finding_by_chunk = {}

    for finding in enriched_findings:

        if (
            finding.scope
            == "production"
            and finding.chunk_id is not None
        ):
            finding_by_chunk.setdefault(
                finding.chunk_id,
                finding,
            )

    cases = []

    for expected_id in expected_ids:

        finding = finding_by_chunk.get(
            expected_id
        )

        if finding is None:
            continue

        case = build_case(
            finding
        )

        if case:
            cases.append(
                case
            )

    print(
        f"Usable cases: "
        f"{len(cases)}"
    )

       # Only production chunks.
    production_chunks = [
        chunk
        for chunk in ast_result.chunks
        if classify_chunk_scope(
            chunk.file
        ) == "production"
    ]

    print(
        f"Production chunks: "
        f"{len(production_chunks)}"
    )

    print(
        "\n=== BUILDING HYBRID RETRIEVER ==="
    )

    retriever = (
        HybridRetriever.build(
            production_chunks
        )
    )

    print(
        "\n=== EVALUATING ==="
    )

    case_results, metrics = (
        evaluate_retrieval(
            retriever=retriever,
            cases=cases,
            top_k=5,
        )
    )

    print(
        "\n=========================="
    )

    print(
        "HYBRID RETRIEVAL RESULTS"
    )

    print(
        "=========================="
    )

    print(
        f"Recall@1: "
        f"{metrics['recall_at_1']:.3f}"
    )

    print(
        f"Recall@3: "
        f"{metrics['recall_at_3']:.3f}"
    )

    print(
        f"Recall@5: "
        f"{metrics['recall_at_5']:.3f}"
    )

    print(
        f"MRR:      "
        f"{metrics['mrr']:.3f}"
    )

    print(
        "\n=== CASE DETAILS ==="
    )

    for index, (
        case,
        result,
    ) in enumerate(
        zip(
            cases,
            case_results,
        ),
        start=1,
    ):

        finding = case.finding

        status = (
            f"rank {result.rank}"
            if result.rank
            else "MISS"
        )

        print(
            f"\n{index:02d}. "
            f"{finding.tool} | "
            f"{finding.file}:"
            f"{finding.line}"
        )

        print(
            finding.message
        )

        print(
            f"Expected: "
            f"{case.expected_chunk_id}"
        )

        print(
            f"Result: "
            f"{status}"
        )

        for rank, chunk_id in enumerate(
            result.retrieved_chunk_ids,
            start=1,
        ):

            marker = (
                " <-- HIT"
                if chunk_id
                == case.expected_chunk_id
                else ""
            )

            print(
                f"  {rank}. "
                f"{chunk_id}"
                f"{marker}"
            )

    output = {
        "repository": REPOSITORY_URL,
        "num_cases": len(cases),
        "metrics": metrics,
        "cases": [
            {
                "finding": (
                    case.finding.__dict__
                ),
                "expected_chunk_id":
                    case.expected_chunk_id,
                "query":
                    case.query,
                "retrieved_chunk_ids":
                    result.retrieved_chunk_ids,
                "rank":
                    result.rank,
                "top_score":
                    result.top_score,
            }
            for case, result in zip(
                cases,
                case_results,
            )
        ],
    }

    RESULT_PATH.write_text(
        json.dumps(
            output,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print(
        f"\nResults saved to: "
        f"{RESULT_PATH}"
    )


if __name__ == "__main__":
    main()