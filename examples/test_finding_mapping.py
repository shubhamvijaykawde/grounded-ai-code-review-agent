from app.analysis.aggregator import (
    analyze_repository,
)
from app.ingestion.github import (
    ingest_repository,
)
from app.parsing.matcher import (
    attach_chunk_references,
    find_best_chunk_for_finding,
)
from app.parsing.python_ast import (
    parse_repository,
)
from app.agent.critic import critique_finding

from app.agent.reviewer import (
    review_findings,
    save_review_results,
)

URL = "https://github.com/pallets/flask"


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

    chunks = ast_result.chunks

    findings = attach_chunk_references(
        report.findings,
        chunks,
    )

    print(
        f"\nFindings: "
        f"{len(findings)}"
    )

    print(
        f"Chunks: "
        f"{len(chunks)}"
    )

    print(
        "\n=== FINDING → CHUNK ==="
    )

    shown = 0

    for finding in findings:

        if finding.line is None:
            continue

        if finding.scope != "production":
            continue

        chunk = (
            find_best_chunk_for_finding(
                finding,
                chunks,
            )
        )

        if chunk is None:
            continue

        print(
            "\nFinding:"
        )

        print(
            f"{finding.tool} | "
            f"{finding.file}:"
            f"{finding.line}"
        )

        print(
            finding.message
        )

        print(
            "\nMatched chunk:"
        )

        print(
            f"{chunk.chunk_type} | "
            f"{chunk.qualified_name}"
        )

        print(
            f"{chunk.file}:"
            f"{chunk.start_line}-"
            f"{chunk.end_line}"
        )

        print(
            "\nCode:"
        )

        print(
            chunk.content[:1000]
        )

        print(
            "=" * 80
        )

        shown += 1

        if shown >= 10:
            break

    print()
    print("=" * 70)
    print("RUNNING REAL CODEROAST AGENT")
    print("=" * 70)

    # Pick a useful production finding.
    target_finding = next(
        (
            finding
            for finding in findings
            if finding.scope == "production"
            and finding.tool == "ruff"
            and finding.rule_id == "BLE001"
            and finding.chunk_id is not None
        ),
        None,
    )

    if target_finding is None:
        raise RuntimeError(
            "Could not find a suitable production Ruff BLE001 finding "
            "with an attached AST chunk."
        )

    # Find the exact AST chunk mapped to the finding.
    target_chunk = next(
        (
            chunk
            for chunk in chunks
            if chunk.chunk_id == target_finding.chunk_id
        ),
        None,
    )

    if target_chunk is None:
        raise RuntimeError(
            f"Could not find AST chunk: {target_finding.chunk_id}"
        )

    print(f"Tool:       {target_finding.tool}")
    print(f"Rule:       {target_finding.rule_id}")
    print(f"File:       {target_finding.file}")
    print(f"Line:       {target_finding.line}")
    print(f"Message:    {target_finding.message}")
    print(f"AST chunk:  {target_chunk.chunk_id}")
    print(f"Function:   {target_chunk.qualified_name}")

    result = critique_finding(
        finding=target_finding,
        target_chunk=target_chunk,
        persona="sarcastic",
    )

    print()
    print("VERDICT:")
    print(result.verdict)

    print()
    print("EXPLANATION:")
    print(result.explanation)

    print()
    print("ROAST:")
    print(result.roast)

    print()
    print("SUGGESTION:")
    print(result.suggestion)

    print()
    print("COMPLIMENT:")
    print(result.compliment)

    print()
    print("EVIDENCE:")
    print(result.evidence_refs)

    print()
    print("GROUNDING:")
    print(result.grounding_status)
    
    print()
    print("=" * 70)
    print("RUNNING REPOSITORY REVIEW")
    print("=" * 70)

    review_results = review_findings(
        findings=findings,
        chunks=chunks,
        max_findings=5,
        persona="sarcastic",
    )

    save_review_results(
        results=review_results,
        output_path="examples/agent_review_results.json",
    )

    print()
    print("=" * 70)
    print("REPOSITORY REVIEW COMPLETE")
    print("=" * 70)

    print(
        f"Generated critiques: {len(review_results)}"
    )

    print(
        "Saved to: examples/agent_review_results.json"
    )


if __name__ == "__main__":
    main()