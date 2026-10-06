from app.agent.models import (
    CritiqueRequest,
    EvidenceItem,
)
from app.parsing.models import CodeChunk
from app.analysis.models import Finding


def finding_to_evidence(finding: Finding) -> EvidenceItem:
    metadata = dict(finding.metadata)

    metadata.update(
        {
            "tool": finding.tool,
            "category": finding.category,
            "severity": finding.severity,
            "rule_id": finding.rule_id,
            "metric_name": finding.metric_name,
            "metric_value": finding.metric_value,
            "scope": finding.scope,
        }
    )

    if finding.code_snippet:
        content = finding.message + "\n\nCode snippet:\n" + finding.code_snippet
    else:
        content = finding.message

    return EvidenceItem(
        evidence_id="finding",
        evidence_type="static_analysis_finding",
        file=finding.file,
        line=finding.line,
        end_line=finding.end_line,
        content=content,
        metadata=metadata,
    )


def chunk_to_evidence(chunk: CodeChunk) -> EvidenceItem:
    metadata = dict(chunk.metadata)

    metadata.update(
        {
            "chunk_type": chunk.chunk_type,
            "name": chunk.name,
            "qualified_name": chunk.qualified_name,
            "parent": chunk.parent,
            "decorators": chunk.decorators,
            "is_async": chunk.is_async,
        }
    )

    return EvidenceItem(
        evidence_id="target_chunk",
        evidence_type="ast_chunk",
        file=chunk.file,
        line=chunk.start_line,
        end_line=chunk.end_line,
        content=chunk.content,
        metadata=metadata,
    )


def build_critique_request(
    finding: Finding,
    target_chunk: CodeChunk,
    context_chunks: list[CodeChunk] | None = None,
    persona: str = "sarcastic",
) -> CritiqueRequest:
    context_chunks = context_chunks or []

    context_evidence = []

    for index, chunk in enumerate(context_chunks, start=1):
        evidence = chunk_to_evidence(chunk)

        evidence.evidence_id = f"context_{index}"

        context_evidence.append(evidence)

    return CritiqueRequest(
        persona=persona,
        finding=finding_to_evidence(finding),
        target_chunk=chunk_to_evidence(target_chunk),
        context_chunks=context_evidence,
    )