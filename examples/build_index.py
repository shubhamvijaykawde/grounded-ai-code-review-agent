from pathlib import Path

from app.ingestion.github import (
    ingest_repository,
)
from app.parsing.python_ast import (
    parse_repository,
)
from app.retrieval.retriever import (
    CodeRetriever,
)
from app.analysis.scope import (
    classify_file_scope,
)


REPOSITORY_URL = (
    "https://github.com/pallets/flask"
)

INDEX_DIR = Path(
    "examples"
) / "rag_index_production"


def main():

    print(
        "=== INGESTION ==="
    )

    repository = ingest_repository(
        REPOSITORY_URL
    )

    print(
        f"Python files: "
        f"{len(repository.files)}"
    )

    print(
        "\n=== AST PARSING ==="
    )

    ast_result = parse_repository(
        repository
    )

    print(
        f"Chunks: "
        f"{len(ast_result.chunks)}"
    )

    production_chunks = [
        chunk
        for chunk in ast_result.chunks
        if classify_file_scope(
            chunk.file
        ) == "production"
    ]

    print(
        f"All chunks: "
        f"{len(ast_result.chunks)}"
    )

    print(
        f"Production chunks: "
        f"{len(production_chunks)}"
    )

    print(
        "\n=== EMBEDDING + FAISS ==="
    )

    retriever = CodeRetriever.build(
        production_chunks
    )

    retriever.save(
        INDEX_DIR
    )

    print(
        "\nIndex saved to:"
    )

    print(
        INDEX_DIR.resolve()
    )


if __name__ == "__main__":
    main()