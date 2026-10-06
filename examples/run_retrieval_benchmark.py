import json
from pathlib import Path

from app.ingestion.github import (
    ingest_repository,
)
from app.analysis.aggregator import (
    analyze_repository,
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
from app.retrieval.embeddings import (
    EmbeddingModel,
)
from app.retrieval.faiss_store import (
    FAISSChunkStore,
)
from app.retrieval.retriever import (
    CodeRetriever,
)


REPOSITORY_URL = (
    "https://github.com/pallets/flask"
)

BENCHMARK_PATH = (
    Path("examples")
    / "retrieval_benchmark.json"
)

INDEX_DIR = (
    Path("examples")
    / "rag_index_production"
)

RESULT_PATH = (
    Path("examples")
    / "retrieval_benchmark_results.json"
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
        "\n=== LOADING REPOSITORY ==="
    )

    repository = ingest_repository(
        REPOSITORY_URL
    )

    print(
        "Running analysis..."
    )

    report = analyze_repository(
        repository
    )

    print(
        "Parsing AST..."
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

    # Map expected chunk IDs back to their findings.
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
            print(
                f"WARNING: could not find "
                f"finding for {expected_id}"
            )
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

    print(
        "\n=== LOADING RAG INDEX ==="
    )

    model = EmbeddingModel()

    store = (
        FAISSChunkStore.load(
            INDEX_DIR
        )
    )

    retriever = CodeRetriever(
        embedding_model=model,
        store=store,
    )

    print(
        f"Indexed chunks: "
        f"{store.index.ntotal}"
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
        "RETRIEVAL RESULTS"
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

        if result.retrieved_chunk_ids:

            print(
                "Top 5:"
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