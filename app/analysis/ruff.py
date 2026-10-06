import json
import subprocess
from pathlib import Path

from app.analysis.scope import classify_file_scope
from app.analysis.models import Finding
from app.analysis.paths import normalize_repository_path
from app.analysis.snippet import get_code_snippet

RUFF_TIMEOUT_SECONDS = 60


def _ruff_severity(rule_id: str) -> str:
    """
    Convert Ruff rule families into our normalized severity.

    This is our application's categorization, not an official
    Ruff severity rating.
    """

    if rule_id.startswith(("F", "B", "S")):
        return "medium"

    return "low"


def run_ruff(workspace: Path) -> list[Finding]:
    """
    Run Ruff against the isolated analysis workspace.

    Ruff is used only for static linting.
    No target repository code is executed.
    """

    command = [
        "ruff",
        "check",
        "--isolated",
        "--no-cache",
        "--output-format",
        "json",
        ".",
    ]

    try:
        result = subprocess.run(
            command,
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            timeout=RUFF_TIMEOUT_SECONDS,
        )

    except FileNotFoundError as exc:
        raise RuntimeError(
            "Ruff was not found. "
            "Install it with: pip install ruff"
        ) from exc

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Ruff analysis timed out."
        ) from exc

    # Ruff normally returns non-zero when lint findings exist.
    # That is not an analysis failure.
    if result.returncode not in (0, 1):
        raise RuntimeError(
            "Ruff failed to analyze the repository.\n"
            f"{result.stderr}"
        )

    if not result.stdout.strip():
        return []

    try:
        diagnostics = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Could not parse Ruff JSON output."
        ) from exc

    findings: list[Finding] = []

    workspace = workspace.resolve()

    for diagnostic in diagnostics:

        filename = diagnostic.get(
            "filename",
            "<unknown>",
        )

        location = diagnostic.get(
            "location",
            {},
        )

        start = location.get(
            "row"
        )

        end_location = diagnostic.get(
            "end_location",
            {},
        )

        end_line = end_location.get(
            "row"
        )

        # Normalize the path to repository-relative form.
        path = Path(filename)

        if path.is_absolute():
            try:
                path = path.resolve().relative_to(workspace)
            except ValueError:
                pass

        normalized_path = normalize_repository_path(
            str(path)
        )

        rule_id = diagnostic.get(
            "code"
        )

        message = diagnostic.get(
            "message",
            "Ruff lint violation.",
        )

        fix = diagnostic.get(
            "fix"
        )

        findings.append(
    Finding(
        tool="ruff",
        category="code_quality",
        severity=_ruff_severity(
            rule_id or ""
        ),
        file=normalized_path,
        line=start,
        end_line=end_line,
        message=message,
        rule_id=rule_id,
        scope=classify_file_scope(
            normalized_path
        ),
        code_snippet=get_code_snippet(
            workspace=workspace,
            file_path=normalized_path,
            line=start,
            end_line=end_line,
        ),
        metadata={
            "url": diagnostic.get("url"),
            "fix_available": fix is not None,
            "severity_source": "code_roaster",
        },
    )
)

    return findings