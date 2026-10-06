from app.analysis.models import Finding
from app.parsing.models import CodeChunk


def chunk_to_embedding_text(
    chunk: CodeChunk,
) -> str:
    """
    Convert an AST chunk into a structured text representation
    for semantic retrieval.
    """

    parts = [
        f"FILE: {chunk.file}",
        f"TYPE: {chunk.chunk_type}",
        f"NAME: {chunk.qualified_name}",
        f"LINES: {chunk.start_line}-{chunk.end_line}",
    ]

    if chunk.parent:
        parts.append(
            f"PARENT: {chunk.parent}"
        )

    if chunk.decorators:
        parts.append(
            "DECORATORS: "
            + ", ".join(chunk.decorators)
        )

    if chunk.docstring:
        parts.append(
            f"DOCSTRING:\n{chunk.docstring}"
        )

    parts.append(
        f"CODE:\n{chunk.content}"
    )

    return "\n".join(parts)


def finding_to_query(
    finding: Finding,
) -> str:
    """
    Convert a static-analysis finding into a semantic search query.
    """

    parts = [
        f"FILE: {finding.file}",
    ]

    if finding.line is not None:
        parts.append(
            f"LINE: {finding.line}"
        )

    if finding.end_line is not None:
        parts.append(
            f"END LINE: {finding.end_line}"
        )

    parts.extend(
        [
            f"TOOL: {finding.tool}",
            f"CATEGORY: {finding.category}",
            f"SEVERITY: {finding.severity}",
        ]
    )

    if finding.rule_id:
        parts.append(
            f"RULE: {finding.rule_id}"
        )

    if finding.metric_name:
        parts.append(
            f"METRIC: {finding.metric_name}"
        )

    if finding.metric_value is not None:
        parts.append(
            f"VALUE: {finding.metric_value}"
        )

    qualified_name = finding.metadata.get(
        "qualified_name"
    )

    if qualified_name:
        parts.append(
            f"QUALIFIED NAME: {qualified_name}"
        )

    parts.append(
        f"MESSAGE: {finding.message}"
    )

    return "\n".join(parts)


def finding_to_semantic_query(
    finding: Finding,
) -> str:
    """
    Create a semantic retrieval query for evaluation.

    IMPORTANT:
    This deliberately excludes:
        - file path
        - line number
        - end line
        - chunk ID
        - qualified name

    Those fields would leak the ground-truth answer.
    """

    parts = [
        f"TOOL: {finding.tool}",
        f"CATEGORY: {finding.category}",
    ]

    if finding.rule_id:
        parts.append(
            f"RULE: {finding.rule_id}"
        )

    if finding.metric_name:
        parts.append(
            f"METRIC: {finding.metric_name}"
        )

    if finding.metric_value is not None:
        parts.append(
            f"VALUE: {finding.metric_value}"
        )

    parts.append(
        f"MESSAGE: {finding.message}"
    )

    return "\n".join(parts)