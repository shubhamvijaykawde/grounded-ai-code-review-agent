from app.ingestion.github import (
    extract_repository_name,
    validate_github_url,
)

from app.ingestion.github_api import (
    calculate_language_percentages,
    parse_github_url,
)


def test_valid_github_url():
    assert validate_github_url(
        "https://github.com/pallets/flask"
    )


def test_invalid_github_url():
    assert not validate_github_url(
        "https://google.com/example/repo"
    )


def test_repository_name():
    assert extract_repository_name(
        "https://github.com/pallets/flask"
    ) == "flask"


def test_repository_name_with_git_suffix():
    assert extract_repository_name(
        "https://github.com/pallets/flask.git"
    ) == "flask"


def test_parse_github_url():

    owner, repository = parse_github_url(
        "https://github.com/pallets/flask"
    )

    assert owner == "pallets"
    assert repository == "flask"


def test_parse_github_url_with_git_suffix():

    owner, repository = parse_github_url(
        "https://github.com/pallets/flask.git"
    )

    assert owner == "pallets"
    assert repository == "flask"


def test_language_percentages():

    result = calculate_language_percentages(
        {
            "Python": 8000,
            "JavaScript": 2000,
        }
    )

    assert result["Python"] == 80.0
    assert result["JavaScript"] == 20.0


def test_empty_language_percentages():

    result = calculate_language_percentages({})

    assert result == {}