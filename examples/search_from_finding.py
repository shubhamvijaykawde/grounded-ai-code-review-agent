from pathlib import Path

from app.analysis.aggregator import (
    analyze_repository,
)
from app.ingestion.github import (
    ingest_repository,
)
from app.parsing.matcher import (
    attach_chunk_references,
)
from app.parsing.python_ast import (
    parse_repository,
)
from app.retrieval.embeddings import (
    EmbeddingModel,
)
from app.retrieval.faiss_store import (
    FAISSChunkStore,
)
from app.retrieval.retriever import (
    CodeRetriever,
)


URL = (
    "https://github.com/pallets/flask"
)

INDEX_DIR = (
    Path("examples")
    / "rag_index"
)


def main():

    print(
        "Ingesting..."
    )

    repository = ingest_repository(
        URL
    )

    print(
        "Analyzing..."
    )

    report = analyze_repository(
        repository
    )

    print(
        "Parsing AST..."
    )

    ast_result = parse_repository(
        repository
    )

    enriched_findings = (
        attach_chunk_references(
            report.findings,
            ast_result.chunks,
        )
    )

    print(
        "\nLoading RAG index..."
    )

    embedding_model = (
        EmbeddingModel()
    )

    store = (
        FAISSChunkStore.load(
            INDEX_DIR
        )
    )

    retriever = CodeRetriever(
        embedding_model=embedding_model,
        store=store,
    )

    print(
        "\n=== FINDING → RAG ==="
    )

    shown = 0

    for finding in enriched_findings:

        if finding.scope != "production":
            continue

        if finding.chunk_id is None:
            continue

        print(
            "\nFinding:"
        )

        print(
            f"{finding.tool} | "
            f"{finding.file}:"
            f"{finding.line}"
        )

        print(
            finding.message
        )

        print(
            f"Matched chunk: "
            f"{finding.metadata.get('qualified_name')}"
        )

        results = (
            retriever.search_finding(
                finding,
                top_k=5,
            )
        )

        print(
            "\nRetrieved:"
        )

        for result in results:

            chunk = result.chunk

            print(
                f"  #{result.rank} "
                f"{result.score:.4f} "
                f"{chunk.qualified_name} "
                f"({chunk.file}:"
                f"{chunk.start_line}-"
                f"{chunk.end_line})"
            )

        print(
            "=" * 80
        )

        shown += 1

        if shown >= 10:
            break


if __name__ == "__main__":
    main()