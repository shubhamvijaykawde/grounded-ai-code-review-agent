from app.parsing.matcher import (
    find_best_chunk_for_finding,
)
from app.parsing.models import CodeChunk
from app.parsing.python_ast import (
    parse_python_file,
)
from app.analysis.models import Finding


TEST_CODE = '''
import pandas as pd

MODEL_VERSION = "1.0"


class MovieRecommender:

    def __init__(self, model):
        self.model = model

    def recommend(self, movie_id):
        result = self.model.predict(movie_id)

        if result:
            return result

        return []


def helper(value):

    def nested(value):
        return value * 2

    return nested(value)
'''


def test_parser_creates_class_and_methods():

    result = parse_python_file(
        "src/recommender.py",
        TEST_CODE,
    )

    assert result.errors == []

    qualified_names = {
        chunk.qualified_name
        for chunk in result.chunks
    }

    assert (
        "MovieRecommender"
        in qualified_names
    )

    assert (
        "MovieRecommender.__init__"
        in qualified_names
    )

    assert (
        "MovieRecommender.recommend"
        in qualified_names
    )


def test_parser_creates_nested_function():

    result = parse_python_file(
        "src/recommender.py",
        TEST_CODE,
    )

    qualified_names = {
        chunk.qualified_name
        for chunk in result.chunks
    }

    assert (
        "helper"
        in qualified_names
    )

    assert (
        "helper.nested"
        in qualified_names
    )


def test_parser_creates_module_chunk():

    result = parse_python_file(
        "src/recommender.py",
        TEST_CODE,
    )

    module_chunks = [
        chunk
        for chunk in result.chunks
        if chunk.chunk_type == "module"
    ]

    assert module_chunks

    combined_content = "\n".join(
        chunk.content
        for chunk in module_chunks
    )

    assert "import pandas as pd" in (
        combined_content
    )

    assert 'MODEL_VERSION = "1.0"' in (
        combined_content
    )


def test_chunk_line_ranges():

    result = parse_python_file(
        "src/recommender.py",
        TEST_CODE,
    )

    for chunk in result.chunks:

        assert chunk.start_line >= 1

        assert (
            chunk.end_line
            >= chunk.start_line
        )

        assert chunk.content


def test_finding_maps_to_specific_method():

    result = parse_python_file(
        "src/recommender.py",
        TEST_CODE,
    )

    finding = Finding(
        tool="radon",
        category="complexity",
        severity="medium",
        file="src/recommender.py",
        line=13,
        end_line=18,
        message="Test complexity finding.",
    )

    chunk = find_best_chunk_for_finding(
        finding,
        result.chunks,
    )

    assert chunk is not None

    assert (
        chunk.qualified_name
        == "MovieRecommender.recommend"
    )


def test_syntax_error_is_captured():

    invalid_code = """
def broken(
    return 123
"""

    result = parse_python_file(
        "broken.py",
        invalid_code,
    )

    assert not result.chunks

    assert len(result.errors) == 1

    assert (
        result.errors[0].file
        == "broken.py"
    )