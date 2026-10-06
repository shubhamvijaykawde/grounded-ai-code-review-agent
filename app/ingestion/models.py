from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SourceFile:
    path: str
    size_bytes: int
    language: str
    content: Optional[str] = None


@dataclass
class RepositoryMetadata:
    name: str
    url: str
    full_name: Optional[str] = None
    description: Optional[str] = None
    default_branch: Optional[str] = None
    commit_count: Optional[int] = None
    stars: Optional[int] = None
    forks: Optional[int] = None
    open_issues: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    size_kb: Optional[int] = None
    languages: Dict[str, float] = field(default_factory=dict)
    is_fork: Optional[bool] = None
    is_archived: Optional[bool] = None


@dataclass
class Repository:
    metadata: RepositoryMetadata
    readme: Optional[str]
    files: List[SourceFile] = field(default_factory=list)