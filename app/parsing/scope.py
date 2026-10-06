from pathlib import PurePosixPath


def classify_chunk_scope(
    file_path: str,
) -> str:
    """
    Classify an AST chunk using its repository-relative file path.
    """

    normalized = (
        file_path
        .replace("\\", "/")
        .strip("/")
    )

    path = PurePosixPath(
        normalized
    )

    parts = path.parts

    if (
        "tests" in parts
        or path.name.startswith("test_")
    ):
        return "tests"

    if "examples" in parts:
        return "examples"

    if "docs" in parts:
        return "other"

    return "production"