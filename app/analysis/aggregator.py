from collections import Counter
from typing import Any

from app.analysis.bandit import run_bandit
from app.analysis.dedup import build_issues, deduplicate_findings
from app.analysis.models import AnalysisReport, Finding
from app.analysis.radon import run_radon
from app.analysis.review import select_review_findings
from app.analysis.ruff import run_ruff
from app.analysis.workspace import (
    materialize_analysis_workspace,
)
from app.ingestion.models import Repository


SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def _sort_findings(
    findings: list[Finding],
) -> list[Finding]:

    return sorted(
        findings,
        key=lambda finding: (
            -SEVERITY_ORDER.get(
                finding.severity,
                0,
            ),
            finding.file,
            finding.line or 0,
        ),
    )


def _build_summary(
    findings: list[Finding],
    review_findings: list[Finding],
) -> dict[str, Any]:

    tool_counts = Counter(
        finding.tool
        for finding in findings
    )

    category_counts = Counter(
        finding.category
        for finding in findings
    )

    severity_counts = Counter(
        finding.severity
        for finding in findings
    )

    scope_counts = Counter(
        finding.scope
        for finding in findings
    )

    production_count = scope_counts.get(
        "production",
        0,
    )

    candidate_count = len(review_findings)

    ignored_low_value_findings = max(
        production_count - candidate_count,
        0,
    )

    ignored_test_findings = scope_counts.get(
        "tests",
        0,
    )

    return {
        "total_findings": len(findings),

        "by_tool": dict(
            tool_counts
        ),

        "by_category": dict(
            category_counts
        ),

        "by_severity": dict(
            severity_counts
        ),

        "by_scope": dict(
            scope_counts
        ),

        "review": {
            "candidate_findings": candidate_count,
            "ignored_test_findings": ignored_test_findings,
            "ignored_low_value_findings": ignored_low_value_findings,
        },
    }


def analyze_repository(
    repository: Repository,
) -> AnalysisReport:
    """
    Run the complete static-analysis pipeline.

    No repository code is executed.
    """

    findings: list[Finding] = []

    # Ruff and Bandit operate on an isolated filesystem workspace.
    with materialize_analysis_workspace(
        repository
    ) as workspace:

        findings.extend(
            run_ruff(workspace)
        )

        findings.extend(
            run_bandit(workspace)
        )

    # Radon operates directly on source strings.
    findings.extend(
        run_radon(repository)
    )

    findings = deduplicate_findings(
        findings
    )

    findings = _sort_findings(
        findings
    )

    review_findings = select_review_findings(
        findings
    )

    review_issues = build_issues(
        review_findings
    )

    summary = _build_summary(
        findings,
        review_findings,
    )

    return AnalysisReport(
        repository_name=repository.metadata.name,
        findings=findings,
        review_findings=review_findings,
        review_issues=review_issues,
        summary=summary,
    )