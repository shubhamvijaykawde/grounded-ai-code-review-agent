import json
from typing import Any
from app.agent.adapters import build_critique_request
from app.parsing.models import CodeChunk
from app.analysis.models import Finding
from app.agent.models import (
    CritiqueRequest,
    CritiqueResponse,
    EvidenceItem,
)
from app.agent.ollama_client import OllamaClient
from app.agent.groq_client import GroqClient
from app.agent.prompts import PERSONAS, SYSTEM_PROMPT_SUFFIX


VALID_PERSONAS = set(PERSONAS.keys())


def _evidence_to_text(item: EvidenceItem) -> str:
    location = item.file or "unknown file"

    if item.line is not None:
        location += f":{item.line}"

        if item.end_line is not None:
            location += f"-{item.end_line}"

    metadata_text = ""

    if item.metadata:
        metadata_text = (
            "\nMetadata:\n"
            + json.dumps(item.metadata, indent=2, default=str)
        )

    return (
        f"Evidence ID: {item.evidence_id}\n"
        f"Type: {item.evidence_type}\n"
        f"Location: {location}\n"
        f"Content:\n{item.content}\n"
        f"{metadata_text}"
    )


def build_user_prompt(request: CritiqueRequest) -> str:
    evidence_blocks = [
        _evidence_to_text(request.finding),
        _evidence_to_text(request.target_chunk),
    ]

    for chunk in request.context_chunks:
        evidence_blocks.append(_evidence_to_text(chunk))

    evidence_text = "\n\n---\n\n".join(evidence_blocks)

    return f"""
Review the following code-review evidence.

PERSONA:
{request.persona}

EVIDENCE:

{evidence_text}

TASK:

Generate a grounded critique based only on the supplied evidence.

The finding was produced by a static-analysis tool.
The target chunk was identified deterministically by our AST mapping.

Do not independently invent additional findings.

Focus on:
1. what was detected,
2. why it matters,
3. what could be improved,
4. one genuine positive observation.

Your response must follow the required JSON structure.
"""


def _parse_response(raw_response: str) -> dict[str, Any]:
    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM response was not valid JSON."
        ) from exc

    if not isinstance(result, dict):
        raise ValueError("LLM response must be a JSON object.")

    required = {
        "verdict",
        "explanation",
        "roast",
        "suggestion",
        "compliment",
        "evidence_refs",
    }

    missing = required - result.keys()

    if missing:
        raise ValueError(
            f"LLM response is missing fields: {sorted(missing)}"
        )

    return result


def validate_grounding(
    result: dict[str, Any],
    request: CritiqueRequest,
) -> str:
    allowed_ids = {
        request.finding.evidence_id,
        request.target_chunk.evidence_id,
    }

    allowed_ids.update(
        chunk.evidence_id
        for chunk in request.context_chunks
    )

    refs = result.get("evidence_refs", [])

    if not isinstance(refs, list):
        return "invalid_reference_format"

    if not all(isinstance(ref, str) for ref in refs):
        return "invalid_reference_format"

    if not set(refs).issubset(allowed_ids):
        return "unsupported_evidence_reference"

    if request.finding.evidence_id not in refs:
        return "missing_finding_reference"

    if request.target_chunk.evidence_id not in refs:
        return "missing_target_reference"

    return "reference_validated"


def critique(
    request: CritiqueRequest,
    client: GroqClient | None = None,
) -> CritiqueResponse:
    persona = request.persona.lower().strip()

    if persona not in VALID_PERSONAS:
        raise ValueError(
            f"Unknown persona '{request.persona}'. "
            f"Choose from: {sorted(VALID_PERSONAS)}"
        )

    client = client or GroqClient()

    system_prompt = (
        PERSONAS[persona]
        + "\n"
        + SYSTEM_PROMPT_SUFFIX
    )

    user_prompt = build_user_prompt(request)

    raw_response = client.chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    result = _parse_response(raw_response)

    grounding_status = validate_grounding(
        result=result,
        request=request,
    )

    return CritiqueResponse(
        verdict=str(result["verdict"]),
        explanation=str(result["explanation"]),
        roast=str(result["roast"]),
        suggestion=str(result["suggestion"]),
        compliment=str(result["compliment"]),
        evidence_refs=list(result["evidence_refs"]),
        grounding_status=grounding_status,
        raw_response=raw_response,
    )

def critique_finding(
    finding: Finding,
    target_chunk: CodeChunk,
    context_chunks: list[CodeChunk] | None = None,
    persona: str = "sarcastic",
    client: GroqClient | None = None,
) -> CritiqueResponse:
    request = build_critique_request(
        finding=finding,
        target_chunk=target_chunk,
        context_chunks=context_chunks,
        persona=persona,
    )

    return critique(
        request=request,
        client=client,
    )