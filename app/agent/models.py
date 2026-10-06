from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceItem:
    evidence_id: str
    evidence_type: str
    file: str | None = None
    line: int | None = None
    end_line: int | None = None
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CritiqueRequest:
    persona: str
    finding: EvidenceItem
    target_chunk: EvidenceItem
    context_chunks: list[EvidenceItem] = field(default_factory=list)


@dataclass
class CritiqueResponse:
    verdict: str
    explanation: str
    roast: str
    suggestion: str
    compliment: str
    evidence_refs: list[str]
    grounding_status: str = "unknown"
    raw_response: str | None = None