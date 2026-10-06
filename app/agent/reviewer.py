from dataclasses import asdict
import json
from pathlib import Path

from app.agent.groq_client import GroqClient
from app.agent.critic import critique_finding
from app.analysis.models import Finding
from app.parsing.models import CodeChunk


SEVERITY_PRIORITY = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

TOOL_PRIORITY = {
    "bandit": 0,
    "ruff": 1,
    "radon": 2,
}


def _finding_key(finding: Finding) -> tuple:
    return (
        finding.tool,
        finding.file,
        finding.line,
        finding.rule_id,
        finding.category,
        finding.message,
    )


def select_review_findings(
    findings: list[Finding],
    max_findings: int = 5,
) -> list[Finding]:
    """
    Select a small but diverse set of production findings.

    Selection prioritizes:
    1. severity
    2. security findings
    3. different tools
    4. different rules/categories
    5. different files
    """

    production = [
        finding
        for finding in findings
        if finding.scope == "production"
        and finding.chunk_id is not None
    ]

    # ---------------------------------------------------------
    # Remove exact duplicates
    # ---------------------------------------------------------

    unique_findings = []
    seen = set()

    for finding in production:

        key = _finding_key(
            finding
        )

        if key in seen:
            continue

        seen.add(key)
        unique_findings.append(
            finding
        )

    # ---------------------------------------------------------
    # Sort by importance
    # ---------------------------------------------------------

    def priority(
        finding: Finding,
    ) -> tuple:

        severity = SEVERITY_PRIORITY.get(
            finding.severity.lower(),
            99,
        )

        tool = TOOL_PRIORITY.get(
            finding.tool.lower(),
            99,
        )

        metric_value = finding.metric_value

        metric_sort = (
            -metric_value
            if metric_value is not None
            else 0
        )

        return (
            severity,
            tool,
            metric_sort,
            finding.file,
            finding.line or 0,
        )

    unique_findings.sort(
        key=priority
    )

    # ---------------------------------------------------------
    # Diverse selection
    # ---------------------------------------------------------

    selected = []

    used_tools = set()
    used_rules = set()
    used_categories = set()
    used_files = set()

    # Pass 1:
    # Guarantee different analysis tools where possible.
    for finding in unique_findings:

        tool = finding.tool.lower()

        if tool in used_tools:
            continue

        selected.append(
            finding
        )

        used_tools.add(tool)
        used_rules.add(
            finding.rule_id
        )
        used_categories.add(
            finding.category
        )
        used_files.add(
            finding.file
        )

        if len(selected) >= max_findings:
            return selected

    # Pass 2:
    # Prefer new rules/categories/files.
    for finding in unique_findings:

        if finding in selected:
            continue

        new_rule = (
            finding.rule_id
            not in used_rules
        )

        new_category = (
            finding.category
            not in used_categories
        )

        new_file = (
            finding.file
            not in used_files
        )

        if new_rule or new_category or new_file:

            selected.append(
                finding
            )

            used_tools.add(
                finding.tool.lower()
            )

            used_rules.add(
                finding.rule_id
            )

            used_categories.add(
                finding.category
            )

            used_files.add(
                finding.file
            )

        if len(selected) >= max_findings:
            return selected

    # Pass 3:
    # Fill any remaining slots.
    for finding in unique_findings:

        if finding in selected:
            continue

        selected.append(
            finding
        )

        if len(selected) >= max_findings:
            break

    return selected

def review_findings(
    findings: list[Finding],
    chunks: list[CodeChunk],
    max_findings: int = 5,
    persona: str = "sarcastic",
    client: GroqClient | None = None,
) -> list[dict]:
    """
    Generate grounded LLM critiques for selected findings.
    """
    client = client or GroqClient()
    selected = select_review_findings(
        findings=findings,
        max_findings=max_findings,
    )

    chunk_by_id = {
        chunk.chunk_id: chunk
        for chunk in chunks
    }

    results = []

    for index, finding in enumerate(selected, start=1):
        print()
        print("=" * 70)
        print(f"REVIEWING FINDING {index}/{len(selected)}")
        print("=" * 70)

        print(
            f"{finding.tool} | "
            f"{finding.file}:{finding.line} | "
            f"{finding.rule_id}"
        )

        print(f"Message: {finding.message}")

        target_chunk = chunk_by_id.get(finding.chunk_id)

        if target_chunk is None:
            print(
                f"WARNING: AST chunk not found: {finding.chunk_id}"
            )
            continue

        print(
            f"Chunk: {target_chunk.qualified_name}"
        )

        try:
            critique = critique_finding(
                finding=finding,
                target_chunk=target_chunk,
                persona=persona,
                client=client,
            )

            review = {
                "finding": {
                    "tool": finding.tool,
                    "category": finding.category,
                    "severity": finding.severity,
                    "file": finding.file,
                    "line": finding.line,
                    "end_line": finding.end_line,
                    "message": finding.message,
                    "metric_name": finding.metric_name,
                    "metric_value": finding.metric_value,
                    "rule_id": finding.rule_id,
                    "scope": finding.scope,
                    "chunk_id": finding.chunk_id,
                    "metadata": finding.metadata,
                },
                "target_chunk": {
                    "chunk_id": target_chunk.chunk_id,
                    "file": target_chunk.file,
                    "chunk_type": target_chunk.chunk_type,
                    "name": target_chunk.name,
                    "qualified_name": target_chunk.qualified_name,
                    "start_line": target_chunk.start_line,
                    "end_line": target_chunk.end_line,
                    "content": target_chunk.content,
                },
                "persona": persona,
                "critique": asdict(critique),
            }

            results.append(review)

            print()
            print("VERDICT:")
            print(critique.verdict)

            print()
            print("ROAST:")
            print(critique.roast)

            print()
            print("GROUNDING:")
            print(critique.grounding_status)

        except Exception as exc:
            print(
                f"ERROR generating critique: {exc}"
            )

    return results


def save_review_results(
    results,
    output_path: str | Path,
) -> None:
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )