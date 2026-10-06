import json
from dataclasses import asdict
from pathlib import Path

from app.ingestion.github import (
    ingest_repository,
)
from app.parsing.python_ast import (
    parse_repository,
)


REPOSITORY_URL = (
    "https://github.com/pallets/flask"
)


def main():

    print(
        "Ingesting repository..."
    )

    repository = ingest_repository(
        REPOSITORY_URL
    )

    print(
        f"Python files: "
        f"{len(repository.files)}"
    )

    print(
        "\nParsing AST..."
    )

    result = parse_repository(
        repository
    )

    print(
        f"Chunks: {len(result.chunks)}"
    )

    print(
        f"Parse errors: "
        f"{len(result.errors)}"
    )

    print(
        "\n=== SAMPLE CHUNKS ==="
    )

    for chunk in result.chunks[:20]:

        print(
            "\n"
            f"{chunk.chunk_type.upper()} | "
            f"{chunk.qualified_name}"
        )

        print(
            f"File: "
            f"{chunk.file}"
        )

        print(
            f"Lines: "
            f"{chunk.start_line}-"
            f"{chunk.end_line}"
        )

        print(
            f"Parent: "
            f"{chunk.parent}"
        )

        print(
            chunk.content[:500]
        )

        print(
            "-" * 70
        )

    output_path = (
        Path("examples")
        / "ast_chunks.json"
    )

    output_path.write_text(
        json.dumps(
            {
                "chunks": [
                    asdict(chunk)
                    for chunk
                    in result.chunks
                ],
                "errors": [
                    asdict(error)
                    for error
                    in result.errors
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"\nSaved AST chunks to: "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()