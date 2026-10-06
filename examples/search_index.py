from pathlib import Path

from app.retrieval.embeddings import (
    EmbeddingModel,
)
from app.retrieval.faiss_store import (
    FAISSChunkStore,
)
from app.retrieval.retriever import (
    CodeRetriever,
)


INDEX_DIR = (
    Path("examples")
    / "rag_index"
)


def main():

    print(
        "Loading FAISS index..."
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

    query = (
        "exception handling and "
        "catching broad Exception "
        "during request dispatch"
    )

    print(
        f"\nQuery:\n{query}"
    )

    results = retriever.search(
        query,
        top_k=5,
    )

    print(
        "\n=== RESULTS ==="
    )

    for result in results:

        chunk = result.chunk

        print(
            f"\n#{result.rank}"
        )

        print(
            f"Score: "
            f"{result.score:.4f}"
        )

        print(
            f"Type: "
            f"{chunk.chunk_type}"
        )

        print(
            f"Name: "
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
            "\n"
            + chunk.content[:700]
        )

        print(
            "\n"
            + "-" * 70
        )


if __name__ == "__main__":
    main()