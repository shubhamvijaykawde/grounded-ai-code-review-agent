from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeChunk:
    """
    A semantically meaningful piece of Python source code.

    Chunks are created from AST nodes rather than arbitrary
    character or line windows.
    """

    chunk_id: str

    file: str

    chunk_type: str

    name: str

    qualified_name: str

    start_line: int

    end_line: int

    content: str

    parent: str | None = None

    docstring: str | None = None

    decorators: list[str] = field(
        default_factory=list
    )

    is_async: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ASTParseError:
    """
    A parsing error for one Python source file.
    """

    file: str

    message: str

    line: int | None = None

    offset: int | None = None


@dataclass
class ASTParseResult:
    """
    AST extraction result for a repository.
    """

    chunks: list[CodeChunk] = field(
        default_factory=list
    )

    errors: list[ASTParseError] = field(
        default_factory=list
    )