from pathlib import Path


def get_code_snippet(
    workspace: Path,
    file_path: str,
    line: int | None,
    end_line: int | None = None,
    context: int = 2,
) -> str | None:
    """
    Extract source code around a finding.

    line numbers are 1-based.
    """

    if line is None:
        return None

    normalized = file_path.replace("\\", "/")

    while normalized.startswith("./"):
        normalized = normalized[2:]

    if normalized.startswith("../"):
        return None

    if normalized == "..":
        return None

    source_path = (
        workspace
        / Path(normalized)
    ).resolve()

    workspace = workspace.resolve()

    try:
        source_path.relative_to(
            workspace
        )
    except ValueError:
        return None

    if not source_path.exists():
        return None

    try:
        lines = source_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()
    except OSError:
        return None

    if not lines:
        return None

    start_line = max(
        1,
        line - context,
    )

    target_end = (
        end_line
        if end_line is not None
        else line
    )

    finish_line = min(
        len(lines),
        target_end + context,
    )

    selected = lines[
        start_line - 1 : finish_line
    ]

    return "\n".join(
        f"{number:>5} | {content}"
        for number, content in zip(
            range(
                start_line,
                finish_line + 1,
            ),
            selected,
        )
    )

def get_code_snippet_from_content(
    content: str,
    line: int | None,
    end_line: int | None = None,
    context: int = 2,
) -> str | None:
    """
    Extract a snippet directly from in-memory source content.

    Used by analyzers (like Radon) that operate on Repository
    objects rather than a materialized filesystem workspace.

    line numbers are 1-based.
    """

    if line is None:
        return None

    lines = content.splitlines()

    if not lines:
        return None

    start_line = max(
        1,
        line - context,
    )

    target_end = (
        end_line
        if end_line is not None
        else line
    )

    finish_line = min(
        len(lines),
        target_end + context,
    )

    selected = lines[
        start_line - 1 : finish_line
    ]

    return "\n".join(
        f"{number:>5} | {content_line}"
        for number, content_line in zip(
            range(
                start_line,
                finish_line + 1,
            ),
            selected,
        )
    )