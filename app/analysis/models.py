from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Finding:
    """
    A normalized static-analysis finding.

    All analysis tools are converted into this common schema.
    """

    tool: str
    category: str
    severity: str

    file: str
    line: Optional[int]

    message: str

    metric_name: Optional[str] = None
    metric_value: Optional[float] = None

    rule_id: Optional[str] = None

    end_line: Optional[int] = None

    code_snippet: Optional[str] = None
        
    scope: str = "production"
        
    chunk_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

@dataclass
class Issue:
    """
    A grouped underlying code issue.

    One issue may have multiple supporting static-analysis findings.
    """

    file: str
    line: int | None
    end_line: int | None

    category: str
    severity: str

    message: str

    findings: list[Finding] = field(
        default_factory=list
    )

    code_snippet: str | None = None

    scope: str = "production"
        
@dataclass
class AnalysisReport:
    """
    Complete static-analysis report for a repository.
    """

    repository_name: str

    findings: list[Finding] = field(default_factory=list)

    review_findings: list[Finding] = field(default_factory=list)
    
    review_issues: list[Issue] = field(default_factory=list)

    summary: dict[str, Any] = field(default_factory=dict)
        
