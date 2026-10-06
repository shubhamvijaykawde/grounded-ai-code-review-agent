from app.parsing.models import CodeChunk
from app.retrieval.embeddings import (
    EmbeddingModel,
)
from app.retrieval.faiss_store import (
    FAISSChunkStore,
)
from app.retrieval.retriever import (
    CodeRetriever,
)


def test_retrieval_returns_relevant_chunk():

    chunks = [
        CodeChunk(
            chunk_id="one",
            file="a.py",
            chunk_type="function",
            name="calculate",
            qualified_name="calculate",
            start_line=1,
            end_line=10,
            content="""
def calculate(value):
    return value * 2
""",
        ),
        CodeChunk(
            chunk_id="two",
            file="b.py",
            chunk_type="function",
            name="handle_error",
            qualified_name="handle_error",
            start_line=1,
            end_line=10,
            content="""
def handle_error(error):
    except_type = Exception
    return str(error)
""",
        ),
    ]

    model = EmbeddingModel()

    from app.retrieval.text import (
        chunk_to_embedding_text,
    )

    texts = [
        chunk_to_embedding_text(
            chunk
        )
        for chunk in chunks
    ]

    embeddings = (
        model.encode_documents(
            texts
        )
    )

    store = (
        FAISSChunkStore.build(
            embeddings,
            chunks,
        )
    )

    retriever = CodeRetriever(
        embedding_model=model,
        store=store,
    )

    results = retriever.search(
        "error handling and Exception",
        top_k=1,
    )

    assert results

    assert (
        results[0].chunk.chunk_id
        == "two"
    )