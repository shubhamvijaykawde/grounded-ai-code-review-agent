def normalize_repository_path(
    path: str,
) -> str:
    """
    Normalize repository paths so that all analyzers
    use the same forward-slash representation.
    """

    normalized = path.replace("\\", "/")

    while normalized.startswith("./"):
        normalized = normalized[2:]

    return normalized