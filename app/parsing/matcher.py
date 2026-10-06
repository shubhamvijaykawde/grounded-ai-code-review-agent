from app.analysis.models import Finding
from app.parsing.models import CodeChunk
from dataclasses import replace

def find_chunks_for_finding(
    finding: Finding,
    chunks: list[CodeChunk],
) -> list[CodeChunk]:
    """
    Find AST chunks that contain a static-analysis finding.

    A finding belongs to a chunk when:

        same file
        AND
        finding line falls inside chunk line range
    """

    if finding.line is None:
        return []

    normalized_file = (
        finding.file
        .replace("\\", "/")
    )

    matches = []

    for chunk in chunks:

        if chunk.file != normalized_file:
            continue

        if (
            chunk.start_line
            <= finding.line
            <= chunk.end_line
        ):
            matches.append(
                chunk
            )

    return matches


def find_best_chunk_for_finding(
    finding: Finding,
    chunks: list[CodeChunk],
) -> CodeChunk | None:
    """
    Return the most specific AST chunk containing a finding.

    When nested chunks overlap, the smallest containing chunk wins.
    """

    matches = find_chunks_for_finding(
        finding,
        chunks,
    )

    if not matches:
        return None

    return min(
        matches,
        key=lambda chunk: (
            chunk.end_line
            - chunk.start_line,
            -chunk.start_line,
        ),
    )


def attach_chunk_references(
    findings: list[Finding],
    chunks: list[CodeChunk],
) -> list[Finding]:
    """
    Attach the best AST chunk reference to each finding.

    The original Finding objects are not mutated. New Finding
    objects are returned with chunk_id populated where a match exists.
    """

    enriched: list[Finding] = []

    for finding in findings:

        chunk = find_best_chunk_for_finding(
            finding,
            chunks,
        )

        if chunk is None:
            enriched.append(
                finding
            )
            continue

        updated_metadata = dict(
            finding.metadata
        )

        updated_metadata.update(
            {
                "chunk_type": chunk.chunk_type,
                "chunk_name": chunk.name,
                "qualified_name": chunk.qualified_name,
                "chunk_start_line": chunk.start_line,
                "chunk_end_line": chunk.end_line,
            }
        )

        enriched.append(
            replace(
                finding,
                chunk_id=chunk.chunk_id,
                metadata=updated_metadata,
            )
        )

    return enriched