import requests


GITHUB_API_BASE = "https://api.github.com"

REQUEST_TIMEOUT = 15


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Extract owner and repository name from a GitHub URL.

    Example:
        https://github.com/pallets/flask
        -> ("pallets", "flask")
    """

    from urllib.parse import urlparse

    parsed = urlparse(url)

    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL.")

    owner = parts[0]
    repository = parts[1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    return owner, repository


def get_repository_metadata(url: str) -> dict:
    """
    Retrieve repository metadata using the GitHub REST API.
    """

    owner, repository = parse_github_url(url)

    api_url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repository}"
    )

    response = requests.get(
        api_url,
        timeout=REQUEST_TIMEOUT,
        headers={
            "Accept": "application/vnd.github+json",
        },
    )

    if response.status_code == 404:
        raise ValueError(
            "GitHub repository was not found or is not publicly accessible."
        )

    response.raise_for_status()

    data = response.json()

    return {
        "name": data.get("name"),
        "full_name": data.get("full_name"),
        "description": data.get("description"),
        "default_branch": data.get("default_branch"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues": data.get("open_issues_count"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "size_kb": data.get("size"),
        "html_url": data.get("html_url"),
        "is_fork": data.get("fork"),
        "is_archived": data.get("archived"),
    }


def get_repository_languages(url: str) -> dict[str, int]:
    """
    Retrieve GitHub's language byte counts for a repository.
    """

    owner, repository = parse_github_url(url)

    api_url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repository}/languages"
    )

    response = requests.get(
        api_url,
        timeout=REQUEST_TIMEOUT,
        headers={
            "Accept": "application/vnd.github+json",
        },
    )

    if response.status_code == 404:
        raise ValueError(
            "GitHub repository was not found or is not publicly accessible."
        )

    response.raise_for_status()

    return response.json()

def calculate_language_percentages(
    languages: dict[str, int],
) -> dict[str, float]:
    """
    Convert GitHub language byte counts into percentages.
    """

    total = sum(languages.values())

    if total == 0:
        return {}

    return {
        language: round((bytes_count / total) * 100, 2)
        for language, bytes_count in languages.items()
    }