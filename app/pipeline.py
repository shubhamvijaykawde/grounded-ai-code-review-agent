from pathlib import Path
from typing import Any

from app.agent.reviewer import (
    review_findings,
    save_review_results,
)
from app.agent.scoring import build_summary
from app.analysis.aggregator import analyze_repository
from app.ingestion.github import ingest_repository
from app.parsing.matcher import attach_chunk_references
from app.parsing.python_ast import parse_repository


def run_code_review(
    repo_url: str,
    persona: str = "sarcastic",
    max_findings: int = 5,
    save_results: bool = True,
) -> dict[str, Any]:
    """
    Run the complete CodeRoast review pipeline.

    The target repository is never executed.
    Static analysis and AST parsing operate on repository source files.
    """

    repo_url = repo_url.strip()

    if not repo_url:
        raise ValueError("GitHub repository URL cannot be empty.")

    if max_findings < 1:
        raise ValueError("max_findings must be at least 1.")

    # ---------------------------------------------------------
    # 1. Ingestion
    # ---------------------------------------------------------

    print("Ingesting repository...")

    repository = ingest_repository(
        repo_url
    )

    # ---------------------------------------------------------
    # 2. Static analysis
    # ---------------------------------------------------------

    print("Running static analysis...")

    analysis_report = analyze_repository(
        repository
    )

    raw_findings = analysis_report.findings

    # ---------------------------------------------------------
    # 3. AST parsing
    # ---------------------------------------------------------

    print("Parsing AST...")

    ast_result = parse_repository(
        repository
    )

    chunks = ast_result.chunks

    # ---------------------------------------------------------
    # 4. Deterministic finding -> AST mapping
    # ---------------------------------------------------------

    print("Mapping findings to AST chunks...")

    findings = attach_chunk_references(
        raw_findings,
        chunks,
    )

    # ---------------------------------------------------------
    # 5. Summary
    # ---------------------------------------------------------

    summary = build_summary(
        findings
    )

    summary["raw_findings"] = len(raw_findings)
    summary["ast_chunks"] = len(chunks)
    summary["ast_parse_errors"] = len(ast_result.errors)

    # ---------------------------------------------------------
    # 6. LLM review
    # ---------------------------------------------------------

    print("Generating grounded critiques...")

    review_results = review_findings(
        findings=findings,
        chunks=chunks,
        max_findings=max_findings,
        persona=persona,
    )

    # ---------------------------------------------------------
    # 7. Repository metadata
    # ---------------------------------------------------------

    metadata = repository.metadata

    repository_info = {
        "name": metadata.name,
        "full_name": metadata.full_name,
        "url": metadata.url,
        "description": metadata.description,
        "default_branch": metadata.default_branch,
        "stars": metadata.stars,
        "forks": metadata.forks,
        "open_issues": metadata.open_issues,
        "languages": metadata.languages,
        "is_fork": metadata.is_fork,
        "is_archived": metadata.is_archived,
    }

    # ---------------------------------------------------------
    # 8. Final result
    # ---------------------------------------------------------

    result = {
        "repository": repository_info,
        "summary": summary,
        "persona": persona,
        "reviewed_findings": review_results,
    }

    # ---------------------------------------------------------
    # 9. Optional JSON output
    # ---------------------------------------------------------

    if save_results:
        save_review_results(
            results=result,
            output_path=Path(
                "examples/code_roast_report.json"
            ),
        )

    return result