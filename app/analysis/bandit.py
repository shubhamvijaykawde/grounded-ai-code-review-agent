import json
import subprocess
from pathlib import Path

from app.analysis.snippet import get_code_snippet
from app.analysis.models import Finding
from app.analysis.scope import classify_file_scope
from app.analysis.paths import normalize_repository_path

BANDIT_TIMEOUT_SECONDS = 60


def run_bandit(workspace: Path) -> list[Finding]:
    """
    Run Bandit recursively over the isolated Python workspace.

    Bandit performs static security analysis and emits JSON.
    """

    command = [
        "bandit",
        "-r",
        ".",
        "-f",
        "json",
        "-q", # <-- add this: suppresses progress/non-JSON output
    ]

    try:
        result = subprocess.run(
        command,
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",   # <-- add this
        timeout=BANDIT_TIMEOUT_SECONDS,
    )

    except FileNotFoundError as exc:
        raise RuntimeError(
            "Bandit was not found. "
            "Install it with: pip install bandit"
        ) from exc

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Bandit analysis timed out."
        ) from exc

    # Bandit returns a non-zero code when issues are found.
    # We therefore parse stdout regardless of a findings-related
    # exit code.
    if not result.stdout.strip():

        if result.returncode == 0:
            return []

        raise RuntimeError(
            "Bandit failed to produce JSON output.\n"
            f"{result.stderr}"
        )

    try:
        report = json.loads(
            result.stdout.lstrip("\ufeff")
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Could not parse Bandit JSON output.\n"
            f"{result.stderr}"
        ) from exc

    findings: list[Finding] = []

    workspace = workspace.resolve()

    for issue in report.get(
        "results",
        [],
    ):

        filename = issue.get(
            "filename",
            "<unknown>",
        )

        path = Path(filename)

        if path.is_absolute():
            try:
                path = path.resolve().relative_to(workspace)
            except ValueError:
                pass

        normalized_path = normalize_repository_path(
            str(path)
        )

        severity = (
            issue.get(
                "issue_severity",
                "LOW",
            )
            .lower()
        )

        confidence = (
            issue.get(
                "issue_confidence"
            )
        )

        line_number = issue.get(
            "line_number"
        )

        line_range = issue.get(
            "line_range",
            [],
        )

        end_line = (
            max(line_range)
            if line_range
            else line_number
        )

        cwe = issue.get(
            "issue_cwe"
        )
        
        snippet = get_code_snippet(
            workspace=workspace,
            file_path=normalized_path,
            line=line_number,
            end_line=end_line,
        ) or issue.get("code")


        findings.append(
            Finding(
                tool="bandit",
                category="security",
                severity=severity,
                file=normalized_path,
                line=line_number,
                end_line=end_line,
                message=issue.get(
                    "issue_text",
                    "Security issue detected.",
                ).strip(),
                rule_id=issue.get(
                    "test_id"
                ),
                code_snippet=snippet,
                scope=classify_file_scope(
                    normalized_path
                ),
                metadata={
                    "test_name": issue.get(
                        "test_name"
                    ),
                    "confidence": confidence,
                    "cwe": cwe,
                    "more_info": issue.get(
                        "more_info"
                    ),
                    "severity_source": "bandit",
                },
            )
        )

    return findings