import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from app.ingestion.models import (
    Repository,
    RepositoryMetadata,
    SourceFile,
)

from app.ingestion.github_api import (
    get_repository_languages,
    get_repository_metadata,
    calculate_language_percentages,
)


MAX_FILES = 500
MAX_FILE_SIZE_BYTES = 1_000_000  # 1 MB
MAX_REPOSITORY_SIZE_BYTES = 50_000_000  # 50 MB


def validate_github_url(url: str) -> bool:
    """
    Validate that the supplied URL points to a GitHub repository.
    """

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return False

    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return False

    # Expected structure:
    # github.com/<owner>/<repository>
    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        return False

    owner, repository = parts[0], parts[1]

    if not owner or not repository:
        return False

    return True


def extract_repository_name(url: str) -> str:
    """
    Extract repository name from a GitHub URL.
    """

    parsed = urlparse(url)
    repository = parsed.path.strip("/").split("/")[-1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    return repository


def clone_repository(url: str, destination: Path) -> None:
    """
    Clone a repository using a shallow clone.

    IMPORTANT:
    The cloned repository is never executed.
    """

    if not validate_github_url(url):
        raise ValueError(f"Invalid GitHub repository URL: {url}")

    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        url,
        str(destination),
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Repository cloning timed out.")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Failed to clone repository:\n{exc.stderr}"
        ) from exc


def calculate_directory_size(directory: Path) -> int:
    """
    Calculate total size of files inside a directory.
    """

    total_size = 0

    for path in directory.rglob("*"):
        if path.is_file():
            try:
                total_size += path.stat().st_size
            except OSError:
                continue

    return total_size


def find_readme(repository_path: Path) -> Optional[str]:
    """
    Find and read the repository README.
    """

    possible_names = [
        "README.md",
        "README.rst",
        "README.txt",
        "README",
    ]

    for name in possible_names:
        readme_path = repository_path / name

        if readme_path.exists() and readme_path.is_file():
            try:
                return readme_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            except OSError:
                return None

    return None


def collect_python_files(repository_path: Path) -> list[SourceFile]:
    """
    Collect Python source files without executing them.
    """

    files: list[SourceFile] = []

    ignored_directories = {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "node_modules",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
    }

    for path in repository_path.rglob("*.py"):

        # Ignore directories we don't want to inspect.
        if any(part in ignored_directories for part in path.parts):
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue

        # Don't load huge files into memory.
        if size > MAX_FILE_SIZE_BYTES:
            continue

        try:
            content = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, UnicodeError):
            continue

        relative_path = path.relative_to(repository_path)

        files.append(
            SourceFile(
                path=str(relative_path),
                size_bytes=size,
                language="Python",
                content=content,
            )
        )

        if len(files) >= MAX_FILES:
            break

    return files


def get_git_commit_count(repository_path: Path) -> Optional[int]:
    """
    Get commit count from the local shallow clone.

    Because we use --depth 1, this will normally be 1.
    Later we can retrieve real GitHub metadata through the API.
    """

    command = [
        "git",
        "-C",
        str(repository_path),
        "rev-list",
        "--count",
        "HEAD",
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )

        return int(result.stdout.strip())

    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
        return None


def ingest_repository(url: str) -> Repository:
    """
    Main repository ingestion function.

    Steps:
        1. Validate URL.
        2. Clone repository.
        3. Check repository size.
        4. Extract README.
        5. Collect Python files.
        6. Return structured Repository object.

    The repository contents are NEVER executed.
    """

    if not validate_github_url(url):
        raise ValueError(
            "Please provide a valid GitHub repository URL."
        )

    repository_name = extract_repository_name(url)

    with tempfile.TemporaryDirectory(prefix="code_roaster_") as temp_dir:

        repository_path = Path(temp_dir) / repository_name

        clone_repository(
            url=url,
            destination=repository_path,
        )

        repository_size = calculate_directory_size(
            repository_path
        )

        if repository_size > MAX_REPOSITORY_SIZE_BYTES:
            raise ValueError(
                f"Repository is too large. "
                f"Maximum allowed size is "
                f"{MAX_REPOSITORY_SIZE_BYTES / 1_000_000:.0f} MB."
            )

        readme = find_readme(repository_path)

        files = collect_python_files(repository_path)

        commit_count = get_git_commit_count(repository_path)

        api_metadata = get_repository_metadata(url)

        languages_raw = get_repository_languages(url)

        languages = calculate_language_percentages(
            languages_raw
        )

        metadata = RepositoryMetadata(
            name=api_metadata["name"],
            url=url,
            full_name=api_metadata["full_name"],
            description=api_metadata["description"],
            default_branch=api_metadata["default_branch"],
            commit_count=commit_count,
            stars=api_metadata["stars"],
            forks=api_metadata["forks"],
            open_issues=api_metadata["open_issues"],
            created_at=api_metadata["created_at"],
            updated_at=api_metadata["updated_at"],
            size_kb=api_metadata["size_kb"],
            languages=languages,
            is_fork=api_metadata["is_fork"],
            is_archived=api_metadata["is_archived"],
        )

        return Repository(
            metadata=metadata,
            readme=readme,
            files=files,
        )