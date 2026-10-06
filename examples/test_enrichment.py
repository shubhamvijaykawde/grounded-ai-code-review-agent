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


URL = (
    "https://github.com/pallets/flask"
)


def main():

    print(
        "Ingesting repository..."
    )

    repository = ingest_repository(
        URL
    )

    print(
        "Running static analysis..."
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

    print(
        "Attaching chunk references..."
    )

    enriched_findings = (
        attach_chunk_references(
            report.findings,
            ast_result.chunks,
        )
    )

    total = len(
        enriched_findings
    )

    matched = sum(
        1
        for finding in enriched_findings
        if finding.chunk_id is not None
    )

    print(
        f"\nFindings: {total}"
    )

    print(
        f"Matched to AST chunk: "
        f"{matched}"
    )

    if total:
        print(
            f"Match rate: "
            f"{matched / total * 100:.2f}%"
        )

    print(
        "\n=== SAMPLE ENRICHED FINDINGS ==="
    )

    shown = 0

    for finding in enriched_findings:

        if finding.chunk_id is None:
            continue

        print(
            "\n"
            f"{finding.tool} | "
            f"{finding.file}:"
            f"{finding.line}"
        )

        print(
            finding.message
        )

        print(
            f"Chunk ID: "
            f"{finding.chunk_id}"
        )

        print(
            f"Qualified name: "
            f"{finding.metadata.get('qualified_name')}"
        )

        print(
            f"Chunk lines: "
            f"{finding.metadata.get('chunk_start_line')}-"
            f"{finding.metadata.get('chunk_end_line')}"
        )

        print(
            "-" * 70
        )

        shown += 1

        if shown >= 10:
            break


if __name__ == "__main__":
    main()