from collections import Counter
from typing import Any
import math


def _severity_counts(findings: list[Any]) -> Counter:
    return Counter(
        str(
            getattr(finding, "severity", "info")
        ).lower()
        for finding in findings
    )


def calculate_score(findings: list[Any]) -> int:
    """
    Calculate an application-level Code Health Score.

    This is intentionally a heuristic score for CodeRoast,
    not a universal software-quality metric.

    Logarithmic penalties prevent large repositories from
    automatically receiving an F simply because they contain
    many low/medium findings.
    """

    counts = _severity_counts(findings)

    critical = counts.get("critical", 0)
    high = counts.get("high", 0)
    medium = counts.get("medium", 0)
    low = counts.get("low", 0)

    penalty = (
        15 * math.log1p(critical)
        + 10 * math.log1p(high)
        + 3 * math.log1p(medium)
        + 0.5 * math.log1p(low)
    )

    score = round(
        max(
            0,
            min(
                100,
                100 - penalty,
            ),
        )
    )

    return score


def grade_from_score(score: int) -> str:
    if score >= 90:
        return "A"

    if score >= 80:
        return "B"

    if score >= 70:
        return "C"

    if score >= 60:
        return "D"

    return "F"


def build_summary(findings: list[Any]) -> dict[str, Any]:

    production = [
        finding
        for finding in findings
        if getattr(
            finding,
            "scope",
            "production",
        ) == "production"
    ]

    severity_counts = _severity_counts(
        production
    )

    tool_counts = Counter(
        str(
            getattr(
                finding,
                "tool",
                "unknown",
            )
        ).lower()
        for finding in production
    )

    categories = Counter(
        str(
            getattr(
                finding,
                "category",
                "unknown",
            )
        )
        for finding in production
    )

    score = calculate_score(
        production
    )

    return {
        "production_findings": len(
            production
        ),
        "score": score,
        "grade": grade_from_score(
            score
        ),
        "severity_counts": dict(
            severity_counts
        ),
        "tool_counts": dict(
            tool_counts
        ),
        "category_counts": dict(
            categories
        ),
    }