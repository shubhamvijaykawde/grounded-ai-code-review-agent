import json

from app.agent.critic import critique
from app.agent.models import (
    CritiqueRequest,
    EvidenceItem,
)


def main() -> None:
    finding = EvidenceItem(
        evidence_id="finding",
        evidence_type="static_analysis_finding",
        file="src/example.py",
        line=42,
        content=(
            "Do not catch blind exception: `Exception`"
        ),
        metadata={
            "tool": "ruff",
            "category": "exception_handling",
            "severity": "medium",
            "rule_id": "BLE001",
        },
    )

    target_chunk = EvidenceItem(
        evidence_id="target_chunk",
        evidence_type="ast_chunk",
        file="src/example.py",
        line=35,
        end_line=50,
        content="""def process_request(data):
    try:
        result = expensive_operation(data)
        return result
    except Exception:
        return None
""",
        metadata={
            "chunk_type": "function",
            "name": "process_request",
            "qualified_name": "process_request",
        },
    )

    request = CritiqueRequest(
        persona="sarcastic",
        finding=finding,
        target_chunk=target_chunk,
    )

    result = critique(request)

    print("\n==============================")
    print("CODEROAST AGENT RESULT")
    print("==============================\n")

    print("Verdict:")
    print(result.verdict)

    print("\nExplanation:")
    print(result.explanation)

    print("\nRoast:")
    print(result.roast)

    print("\nSuggestion:")
    print(result.suggestion)

    print("\nCompliment:")
    print(result.compliment)

    print("\nEvidence refs:")
    print(result.evidence_refs)

    print("\nGrounding:")
    print(result.grounding_status)

    print("\nRaw JSON:")
    print(json.dumps(
        {
            "verdict": result.verdict,
            "explanation": result.explanation,
            "roast": result.roast,
            "suggestion": result.suggestion,
            "compliment": result.compliment,
            "evidence_refs": result.evidence_refs,
            "grounding_status": result.grounding_status,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()