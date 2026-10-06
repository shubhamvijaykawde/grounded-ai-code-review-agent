from app.analysis.aggregator import (
    analyze_repository,
)
from app.ingestion.models import (
    Repository,
    RepositoryMetadata,
    SourceFile,
)


TEST_CODE = """
import os


def extremely_complex_function(
    a, b, c, d, e, f, g, h, i, j, k
):
    if a:
        pass

    if b:
        pass

    if c:
        pass

    if d:
        pass

    if e:
        pass

    if f:
        pass

    if g:
        pass

    if h:
        pass

    if i:
        pass

    if j:
        pass

    if k:
        pass

    return eval(a)
"""


def build_test_repository() -> Repository:

    metadata = RepositoryMetadata(
        name="analysis-fixture",
        url="https://github.com/example/example",
    )

    source_file = SourceFile(
        path="example.py",
        size_bytes=len(
            TEST_CODE.encode("utf-8")
        ),
        language="Python",
        content=TEST_CODE,
    )

    return Repository(
        metadata=metadata,
        readme=None,
        files=[source_file],
    )


def test_analysis_returns_report():

    repository = (
        build_test_repository()
    )

    report = analyze_repository(
        repository
    )

    assert (
        report.repository_name
        == "analysis-fixture"
    )

    assert isinstance(
        report.findings,
        list,
    )

    assert (
        report.summary["total_findings"]
        == len(report.findings)
    )


def test_ruff_finds_unused_import():

    repository = (
        build_test_repository()
    )

    report = analyze_repository(
        repository
    )

    assert any(
        finding.tool == "ruff"
        and finding.rule_id == "F401"
        for finding in report.findings
    )


def test_radon_finds_high_complexity():

    repository = (
        build_test_repository()
    )

    report = analyze_repository(
        repository
    )

    assert any(
        finding.tool == "radon"
        and finding.metric_name
        == "cyclomatic_complexity"
        and finding.metric_value >= 11
        for finding in report.findings
    )


def test_bandit_finds_security_issue():

    repository = (
        build_test_repository()
    )

    report = analyze_repository(
        repository
    )

    assert any(
        finding.tool == "bandit"
        and finding.category == "security"
        for finding in report.findings
    )