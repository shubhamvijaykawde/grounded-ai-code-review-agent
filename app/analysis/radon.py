from radon.complexity import cc_rank, cc_visit
from radon.metrics import mi_visit

from app.analysis.models import Finding
from app.ingestion.models import Repository
from app.analysis.scope import classify_file_scope
from app.analysis.paths import normalize_repository_path
from app.analysis.snippet import get_code_snippet_from_content


def _complexity_severity(rank: str) -> str:
    """
    Convert Radon's complexity rank to our normalized severity.
    """

    if rank in {"A", "B"}:
        return "low"

    if rank == "C":
        return "medium"

    if rank == "D":
        return "high"

    return "critical"


def _maintainability_rank(score: float) -> str:
    """
    Radon's documented MI ranges:

    A: 20-100
    B: 10-19
    C: 0-9
    """

    if score >= 20:
        return "A"

    if score >= 10:
        return "B"

    return "C"


def _maintainability_severity(rank: str) -> str:

    if rank == "A":
        return "low"

    if rank == "B":
        return "medium"

    return "high"


def run_radon(repository: Repository) -> list[Finding]:
    """
    Run Radon's cyclomatic-complexity and maintainability
    analysis over the Python source contained in the Repository object.

    We flag:
      - complexity >= 11
      - maintainability index < 20
    """

    findings: list[Finding] = []

    for source_file in repository.files:

        if source_file.language != "Python":
            continue

        content = source_file.content or ""

        if not content.strip():
            continue
            
        normalized_path = normalize_repository_path(
            source_file.path
        )

        # ---------------------------------------------------------
        # Cyclomatic Complexity
        # ---------------------------------------------------------

        try:
            blocks = cc_visit(content)

            for block in blocks:

                complexity = block.complexity
                rank = cc_rank(complexity)

                # Only report moderate or worse complexity.
                if complexity < 11:
                    continue

                classname = getattr(
                    block,
                    "classname",
                    None,
                )

                if classname:
                    block_name = (
                        f"{classname}.{block.name}"
                    )
                else:
                    block_name = block.name

                findings.append(
                    Finding(
                        tool="radon",
                        category="complexity",
                        severity=_complexity_severity(
                            rank
                        ),
                        file = normalized_path,
                        line=block.lineno,
                        end_line=getattr(
                            block,
                            "endline",
                            None,
                        ),
                        message=(
                            f"{block_name} has "
                            f"cyclomatic complexity "
                            f"{complexity} "
                            f"(rank {rank})."
                        ),
                        metric_name=(
                            "cyclomatic_complexity"
                        ),
                        metric_value=float(
                            complexity
                        ),
                        scope=classify_file_scope(
                            normalized_path
                        ),
                        code_snippet=get_code_snippet_from_content(
                            content=content,
                            line=block.lineno,
                            end_line=getattr(
                                block,
                                "endline",
                                None,
                            ),
                        ),
                        metadata={
                            "rank": rank,
                            "block_type": block.__class__.__name__,
                            "name": block.name,
                            "classname": classname,
                            "severity_source": "code_roaster",
                        },
                    )
                )

        except SyntaxError as exc:

            findings.append(
                Finding(
                    tool="radon",
                    category="parsing",
                    severity="medium",
                    file=normalized_path,
                    line=getattr(
                        exc,
                        "lineno",
                        None,
                    ),
                    message=(
                        "Radon could not parse this "
                        f"Python file: {exc.msg}"
                    ),
                    metadata={
                        "error": str(exc),
                        "severity_source": "code_roaster",
                    },
                )
            )

        # ---------------------------------------------------------
        # Maintainability Index
        # ---------------------------------------------------------

        try:

            mi_score = float(
                mi_visit(
                    content,
                    multi=True,
                )
            )

            mi_score = round(
                mi_score,
                2,
            )

            rank = _maintainability_rank(
                mi_score
            )

            # Only report lower-maintainability files.
            if mi_score < 20:

                findings.append(
                    Finding(
                        tool="radon",
                        category="maintainability",
                        severity=_maintainability_severity(
                            rank
                        ),
                        file=normalized_path,
                        line=None,
                        message=(
                            f"Maintainability Index is "
                            f"{mi_score} "
                            f"(rank {rank})."
                        ),
                        metric_name=(
                            "maintainability_index"
                        ),
                        metric_value=mi_score,
                        scope=classify_file_scope(
                            normalized_path
                        ),
                        code_snippet=None,
                        metadata={
                            "rank": rank,
                            "severity_source": "code_roaster",
                        },
                    )
                )

        except (SyntaxError, ValueError):

            # A parsing finding above already captures the problem.
            pass

    return findings