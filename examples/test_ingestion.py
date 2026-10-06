from app.ingestion.github import ingest_repository


URL = "https://github.com/pallets/flask"


def main():
    repository = ingest_repository(URL)

    print("\n=== REPOSITORY ===")
    print(repository.metadata)

    print("\n=== README ===")

    if repository.readme:
        print(repository.readme[:1000])
    else:
        print("No README found.")

    print("\n=== PYTHON FILES ===")

    for file in repository.files:
        print(
            f"{file.path} | "
            f"{file.size_bytes} bytes | "
            f"{file.language}"
        )

    print(f"\nTotal Python files: {len(repository.files)}")


if __name__ == "__main__":
    main()