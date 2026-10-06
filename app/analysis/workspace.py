from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from app.ingestion.models import Repository


IGNORED_FILE_NAMES = {
    ".gitignore",
}


@contextmanager
def materialize_analysis_workspace(
    repository: Repository,
) -> Iterator[Path]:
    """
    Materialize repository source files into a temporary workspace.

    The workspace contains only the source files collected by our
    ingestion layer. No repository dependencies, executables, or
    configuration files are copied.

    The workspace is automatically deleted afterwards.
    """

    with TemporaryDirectory(
        prefix="code_roaster_analysis_"
    ) as temp_dir:

        workspace = Path(temp_dir).resolve()

        for source_file in repository.files:

            relative_path = Path(source_file.path)

            # Only allow relative paths.
            if relative_path.is_absolute():
                continue

            # Prevent path traversal.
            if ".." in relative_path.parts:
                continue

            # We currently support Python only.
            if relative_path.suffix.lower() != ".py":
                continue

            # Avoid special unwanted files.
            if relative_path.name in IGNORED_FILE_NAMES:
                continue

            destination = (
                workspace / relative_path
            ).resolve()

            # Make absolutely sure the destination remains
            # inside our temporary workspace.
            try:
                destination.relative_to(workspace)
            except ValueError:
                continue

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            content = source_file.content or ""

            destination.write_text(
                content,
                encoding="utf-8",
            )

        yield workspace