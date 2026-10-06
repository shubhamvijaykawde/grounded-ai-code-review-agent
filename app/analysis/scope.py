from pathlib import Path


def classify_file_scope(file_path: str) -> str:
    """
    Classify a repository file into an analysis scope.

    Current scopes:
        production
        tests
        examples
        other
    """

    normalized = (
        file_path
        .replace("\\", "/")
        .strip("/")
    )

    parts = normalized.split("/")

    if "tests" in parts or Path(normalized).name.startswith(
        "test_"
    ):
        return "tests"

    if "examples" in parts:
        return "examples"

    if "docs" in parts:
        return "other"

    return "production"