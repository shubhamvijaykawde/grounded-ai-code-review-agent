from app.ingestion.github_api import (
    get_repository_metadata,
    get_repository_languages,
    calculate_language_percentages,
)


URL = "https://github.com/pallets/flask"


def main():

    print("\n=== REPOSITORY METADATA ===")

    metadata = get_repository_metadata(URL)

    for key, value in metadata.items():
        print(f"{key}: {value}")

    print("\n=== LANGUAGES ===")

    languages = get_repository_languages(URL)

    print(languages)

    print("\n=== LANGUAGE PERCENTAGES ===")

    percentages = calculate_language_percentages(
        languages
    )

    for language, percentage in percentages.items():
        print(f"{language}: {percentage}%")


if __name__ == "__main__":
    main()