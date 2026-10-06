import json
from collections import defaultdict
from dataclasses import asdict
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
)


REPOSITORY_URL = (
    "https://github.com/pallets/flask"
)

OUTPUT_PATH = (
    Path("examples")
    / "retrieval_benchmark.json"
)

MAX_CASES = 30


SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def main():

    print(
        "=== INGESTION ==="
    )

    repository = ingest_repository(
        REPOSITORY_URL
    )

    print(
        "=== ANALYSIS ==="
    )

    report = analyze_repository(
        repository
    )

    print(
        "=== AST ==="
    )

    ast_result = parse_repository(
        repository
    )

    print(
        "=== ENRICHMENT ==="
    )

    findings = attach_chunk_references(
        report.findings,
        ast_result.chunks,
    )

    # Only production findings with exact AST anchors.
    candidates = [
        finding
        for finding in findings
        if finding.scope == "production"
        and finding.chunk_id is not None
    ]

    print(
        f"Production candidates: "
        f"{len(candidates)}"
    )

    # Keep the strongest finding per chunk + rule.
    unique: dict[
        tuple[str, str | None],
        object,
    ] = {}

    for finding in candidates:

        key = (
            finding.chunk_id,
            finding.rule_id,
        )

        existing = unique.get(key)

        if existing is None:
            unique[key] = finding
            continue

        current_score = (
            SEVERITY_ORDER.get(
                finding.severity,
                0,
            )
        )

        existing_score = (
            SEVERITY_ORDER.get(
                existing.severity,
                0,
            )
        )

        if current_score > existing_score:
            unique[key] = finding

    candidates = list(
        unique.values()
    )

    # Group by broad category so the benchmark isn't
    # accidentally dominated by one detector type.
    by_category = defaultdict(list)

    for finding in candidates:
        by_category[finding.category].append(
            finding
        )

    # Sort each category by severity.
    for category in by_category:

        by_category[category].sort(
            key=lambda finding: (
                -SEVERITY_ORDER.get(
                    finding.severity,
                    0,
                ),
                finding.file,
                finding.line or 0,
            )
        )

    selected = []

    # Round-robin across categories.
    while (
        len(selected) < MAX_CASES
        and any(by_category.values())
    ):

        for category in list(
            by_category.keys()
        ):

            items = by_category[
                category
            ]

            if not items:
                del by_category[
                    category
                ]
                continue

            finding = items.pop(0)

            case = build_case(
                finding
            )

            if case is not None:
                selected.append(
                    case
                )

            if len(selected) >= MAX_CASES:
                break

    benchmark = {
        "repository": REPOSITORY_URL,
        "num_cases": len(selected),
        "cases": [
            {
                "expected_chunk_id":
                    case.expected_chunk_id,

                "query":
                    case.query,

                "finding": asdict(
                    case.finding
                ),
            }
            for case in selected
        ],
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            benchmark,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"\nBenchmark cases: "
        f"{len(selected)}"
    )

    print(
        f"Saved to: "
        f"{OUTPUT_PATH}"
    )

    print(
        "\n=== CASES ==="
    )

    for index, case in enumerate(
        selected,
        start=1,
    ):

        finding = case.finding

        print(
            f"{index:02d}. "
            f"{finding.tool:6s} | "
            f"{finding.category:15s} | "
            f"{finding.file}:"
            f"{finding.line}"
        )

        print(
            f"    expected: "
            f"{case.expected_chunk_id}"
        )


if __name__ == "__main__":
    main()