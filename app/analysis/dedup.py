from collections import defaultdict

from app.analysis.models import Finding

from app.analysis.models import Finding, Issue

def finding_key(finding: Finding) -> tuple:
    """
    Identify findings that refer to approximately the same source location.

    We intentionally ignore the tool and rule ID here because different
    tools may identify the same underlying issue.
    """

    return (
        finding.file,
        finding.line,
        finding.end_line,
        finding.category,
    )


def deduplicate_findings(
    findings: list[Finding],
) -> list[Finding]:
    """
    Remove exact duplicate findings.

    Findings from different tools are NOT merged here. Instead, this
    function only removes identical normalized findings.

    Cross-tool correlation is handled separately.
    """

    seen: set[tuple] = set()
    result: list[Finding] = []

    for finding in findings:

        key = (
            finding.tool,
            finding.file,
            finding.line,
            finding.end_line,
            finding.rule_id,
            finding.message,
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(finding)

    return result


def group_related_findings(
    findings: list[Finding],
) -> list[list[Finding]]:
    """
    Group findings referring to the same file/location/category.

    Example:

        Ruff S102
        Bandit B102

    can become one group containing two detector findings.
    """

    groups: dict[
        tuple,
        list[Finding]
    ] = defaultdict(list)

    for finding in findings:
        groups[finding_key(finding)].append(
            finding
        )

    return list(groups.values())

SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def build_issues(
    findings: list[Finding],
) -> list[Issue]:

    groups = group_related_findings(
        findings
    )

    issues: list[Issue] = []

    for group in groups:

        # Pick the strongest severity among
        # the supporting detector findings.
        representative = max(
            group,
            key=lambda finding: SEVERITY_ORDER.get(
                finding.severity,
                0,
            ),
        )

        # Prefer a source snippet that actually exists.
        snippet = next(
            (
                finding.code_snippet
                for finding in group
                if finding.code_snippet
            ),
            None,
        )

        issues.append(
            Issue(
                file=representative.file,
                line=representative.line,
                end_line=representative.end_line,
                category=representative.category,
                severity=representative.severity,
                message=representative.message,
                findings=group,
                code_snippet=snippet,
                scope=representative.scope,
            )
        )

    return issues