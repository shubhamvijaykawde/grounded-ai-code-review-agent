from app.analysis.models import Finding


IGNORED_LOW_VALUE_RULES = {
    "B101",  # assert_used
}


def select_review_findings(
    findings: list[Finding],
) -> list[Finding]:
    """
    Select findings that are appropriate for the AI review.

    Raw findings remain untouched.
    """

    selected = []

    for finding in findings:

        # Focus the review on production code.
        if finding.scope != "production":
            continue

        # Avoid extremely noisy rules.
        if finding.rule_id in IGNORED_LOW_VALUE_RULES:
            continue

        selected.append(finding)

    return selected