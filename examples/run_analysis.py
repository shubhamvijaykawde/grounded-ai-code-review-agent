import json
from dataclasses import asdict
from pathlib import Path

from app.analysis.aggregator import (
    analyze_repository,
)
from app.ingestion.github import (
    ingest_repository,
)


REPOSITORY_URL = (
    "https://github.com/pallets/flask"
)


def main():

    print(
        "Ingesting repository..."
    )

    repository = ingest_repository(
        REPOSITORY_URL
    )

    print(
        f"Found {len(repository.files)} "
        f"Python files."
    )

    print(
        "\nRunning static analysis..."
    )

    report = analyze_repository(
        repository
    )

    print(
        "\n=== SUMMARY ==="
    )

    print(
        json.dumps(
            report.summary,
            indent=2,
        )
    )

    print(
        "\n=== REVIEW ISSUES ==="
    )

    for issue in report.review_issues[:20]:

        location = issue.file

        if issue.line:
            location += (
                f":{issue.line}"
            )

        print(
            f"\n[{issue.severity.upper()}] "
            f"{location}"
        )

        print(
            issue.message
        )

        tools = ", ".join(
            finding.tool
            for finding in issue.findings
        )

        print(
            f"Detected by: {tools}"
        )

    # Save machine-readable report.
    output_path = (
        Path("examples")
        / "analysis_report.json"
    )

    output_path.write_text(
        json.dumps(
            asdict(report),
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"\nFull report saved to: "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()