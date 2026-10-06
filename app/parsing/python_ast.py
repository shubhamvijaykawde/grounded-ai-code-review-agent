import ast
from pathlib import Path

from app.ingestion.models import Repository
from app.parsing.models import (
    ASTParseError,
    ASTParseResult,
    CodeChunk,
)


FUNCTION_NODES = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
)

CONTAINER_NODES = (
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
)


def _extract_source(
    content: str,
    start_line: int,
    end_line: int,
) -> str:
    """
    Extract source code using 1-based inclusive line numbers.
    """

    lines = content.splitlines()

    if not lines:
        return ""

    start_line = max(
        1,
        start_line,
    )

    end_line = min(
        len(lines),
        end_line,
    )

    if end_line < start_line:
        return ""

    return "\n".join(
        lines[start_line - 1:end_line]
    )


def _node_start_line(
    node: ast.AST,
) -> int:
    """
    Return the earliest source line belonging to an AST node.

    For decorated functions/classes, include decorator lines.
    """

    line = getattr(
        node,
        "lineno",
        1,
    )

    decorators = getattr(
        node,
        "decorator_list",
        [],
    )

    if decorators:

        decorator_lines = [
            getattr(
                decorator,
                "lineno",
                line,
            )
            for decorator in decorators
        ]

        line = min(
            [line, *decorator_lines]
        )

    return line


def _node_end_line(
    node: ast.AST,
) -> int:
    """
    Return the final source line belonging to an AST node.
    """

    end_line = getattr(
        node,
        "end_lineno",
        None,
    )

    if end_line is None:
        return getattr(
            node,
            "lineno",
            1,
        )

    return end_line


def _get_docstring(
    node: ast.AST,
) -> str | None:
    """
    Extract a node's docstring when available.
    """

    if isinstance(
        node,
        (
            ast.Module,
            ast.ClassDef,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    ):
        return ast.get_docstring(
            node,
            clean=True,
        )

    return None


def _get_decorators(
    node: ast.AST,
) -> list[str]:
    """
    Return decorator expressions as source-like strings.

    ast.unparse() is only applied to the AST node itself.
    It does not execute repository code.
    """

    decorators = getattr(
        node,
        "decorator_list",
        [],
    )

    result = []

    for decorator in decorators:

        try:
            result.append(
                ast.unparse(
                    decorator
                )
            )
        except Exception:
            result.append(
                "<unparseable decorator>"
            )

    return result


def _make_chunk_id(
    file_path: str,
    qualified_name: str,
    start_line: int,
) -> str:
    """
    Create a deterministic chunk identifier.
    """

    normalized_path = (
        file_path
        .replace("\\", "/")
    )

    return (
        f"{normalized_path}"
        f"::{qualified_name}"
        f"::{start_line}"
    )


class PythonASTVisitor(ast.NodeVisitor):
    """
    Traverse a Python AST and produce semantic code chunks.

    We keep track of class/function scope so nested definitions
    receive useful qualified names such as:

        Blueprint.register
        outer_function.inner_function
        MyClass.method
    """

    def __init__(
        self,
        file_path: str,
        content: str,
    ) -> None:

        self.file_path = (
            file_path
            .replace("\\", "/")
        )

        self.content = content

        self.chunks: list[CodeChunk] = []

        self.scope_stack: list[str] = []

        self.class_stack: list[str] = []

        self.function_stack: list[str] = []

    def _qualified_name(
        self,
        name: str,
    ) -> str:

        if not self.scope_stack:
            return name

        return ".".join(
            [*self.scope_stack, name]
        )

    def _add_definition_chunk(
        self,
        node: ast.AST,
        chunk_type: str,
        name: str,
    ) -> None:

        start_line = _node_start_line(
            node
        )

        end_line = _node_end_line(
            node
        )

        qualified_name = (
            self._qualified_name(name)
        )

        content = _extract_source(
            self.content,
            start_line,
            end_line,
        )

        parent = (
            ".".join(
                self.scope_stack
            )
            if self.scope_stack
            else None
        )

        chunk = CodeChunk(
            chunk_id=_make_chunk_id(
                self.file_path,
                qualified_name,
                start_line,
            ),
            file=self.file_path,
            chunk_type=chunk_type,
            name=name,
            qualified_name=qualified_name,
            start_line=start_line,
            end_line=end_line,
            content=content,
            parent=parent,
            docstring=_get_docstring(
                node
            ),
            decorators=_get_decorators(
                node
            ),
            is_async=isinstance(
                node,
                ast.AsyncFunctionDef,
            ),
            metadata={
                "node_type": (
                    node.__class__.__name__
                ),
            },
        )

        self.chunks.append(
            chunk
        )

    def visit_ClassDef(
        self,
        node: ast.ClassDef,
    ) -> None:

        self._add_definition_chunk(
            node=node,
            chunk_type="class",
            name=node.name,
        )

        self.scope_stack.append(
            node.name
        )

        self.class_stack.append(
            node.name
        )

        self.generic_visit(
            node
        )

        self.class_stack.pop()

        self.scope_stack.pop()

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> None:

        if self.class_stack:
            if self.function_stack:
                chunk_type = (
                    "nested_function"
                )
            else:
                chunk_type = "method"

        elif self.function_stack:
            chunk_type = (
                "nested_function"
            )

        else:
            chunk_type = "function"

        self._add_definition_chunk(
            node=node,
            chunk_type=chunk_type,
            name=node.name,
        )

        self.scope_stack.append(
            node.name
        )

        self.function_stack.append(
            node.name
        )

        self.generic_visit(
            node
        )

        self.function_stack.pop()

        self.scope_stack.pop()

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:

        if self.class_stack:
            if self.function_stack:
                chunk_type = (
                    "nested_function"
                )
            else:
                chunk_type = "method"

        elif self.function_stack:
            chunk_type = (
                "nested_function"
            )

        else:
            chunk_type = "function"

        self._add_definition_chunk(
            node=node,
            chunk_type=chunk_type,
            name=node.name,
        )

        self.scope_stack.append(
            node.name
        )

        self.function_stack.append(
            node.name
        )

        self.generic_visit(
            node
        )

        self.function_stack.pop()

        self.scope_stack.pop()


def _create_module_chunks(
    file_path: str,
    content: str,
    tree: ast.Module,
) -> list[CodeChunk]:
    """
    Create chunks for top-level statements that are not
    functions or classes.

    This typically captures:

        imports
        module constants
        configuration
        top-level assignments
        if __name__ == "__main__"
    """

    chunks: list[CodeChunk] = []

    current_nodes: list[ast.AST] = []

    def flush() -> None:

        if not current_nodes:
            return

        first = current_nodes[0]
        last = current_nodes[-1]

        start_line = _node_start_line(
            first
        )

        end_line = _node_end_line(
            last
        )

        chunk_content = _extract_source(
            content,
            start_line,
            end_line,
        )

        chunk_number = (
            len(chunks) + 1
        )

        qualified_name = (
            f"<module>.section_{chunk_number}"
        )

        chunks.append(
            CodeChunk(
                chunk_id=_make_chunk_id(
                    file_path,
                    qualified_name,
                    start_line,
                ),
                file=file_path.replace(
                    "\\",
                    "/",
                ),
                chunk_type="module",
                name=f"section_{chunk_number}",
                qualified_name=qualified_name,
                start_line=start_line,
                end_line=end_line,
                content=chunk_content,
                metadata={
                    "node_type": "ModuleSection",
                },
            )
        )

        current_nodes.clear()

    for node in tree.body:

        if isinstance(
            node,
            CONTAINER_NODES,
        ):
            flush()
            continue

        current_nodes.append(
            node
        )

    flush()

    return chunks


def parse_python_file(
    file_path: str,
    content: str,
) -> ASTParseResult:
    """
    Parse one Python source file into semantic chunks.

    This function only parses source text.
    It does not import or execute the source file.
    """

    normalized_path = (
        file_path
        .replace("\\", "/")
    )

    if not content.strip():
        return ASTParseResult()

    try:
        tree = ast.parse(
            content,
            filename=normalized_path,
            type_comments=True,
        )

    except SyntaxError as exc:

        return ASTParseResult(
            errors=[
                ASTParseError(
                    file=normalized_path,
                    message=exc.msg,
                    line=exc.lineno,
                    offset=exc.offset,
                )
            ]
        )

    except (
        ValueError,
        MemoryError,
        RecursionError,
    ) as exc:

        return ASTParseResult(
            errors=[
                ASTParseError(
                    file=normalized_path,
                    message=(
                        "AST parsing failed: "
                        f"{exc}"
                    ),
                )
            ]
        )

    module_chunks = _create_module_chunks(
        file_path=normalized_path,
        content=content,
        tree=tree,
    )

    visitor = PythonASTVisitor(
        file_path=normalized_path,
        content=content,
    )

    visitor.visit(
        tree
    )

    chunks = [
        *module_chunks,
        *visitor.chunks,
    ]

    chunks.sort(
        key=lambda chunk: (
            chunk.start_line,
            chunk.end_line,
            chunk.chunk_type,
        )
    )

    return ASTParseResult(
        chunks=chunks
    )


def parse_repository(
    repository: Repository,
) -> ASTParseResult:
    """
    Parse all Python files in a Repository object.
    """

    all_chunks: list[CodeChunk] = []
    all_errors: list[ASTParseError] = []

    for source_file in repository.files:

        if source_file.language != "Python":
            continue

        result = parse_python_file(
            file_path=source_file.path,
            content=source_file.content or "",
        )

        all_chunks.extend(
            result.chunks
        )

        all_errors.extend(
            result.errors
        )

    return ASTParseResult(
        chunks=all_chunks,
        errors=all_errors,
    )