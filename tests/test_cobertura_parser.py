"""Tests for the Cobertura parser module."""

from __future__ import annotations

import textwrap

import pytest

from src.analyzers.cobertura_parser import CoberturaParser


@pytest.fixture()
def parser() -> CoberturaParser:
    return CoberturaParser()


def _write_xml(tmp_path, content: str) -> str:
    xml_path = tmp_path / "coverage.xml"
    xml_path.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(xml_path)


def test_parse_coverage_file_returns_expected_structure(parser: CoberturaParser, tmp_path):
    xml_path = _write_xml(
        tmp_path,
        """
        <coverage line-rate="0.5" branch-rate="0.25" lines-covered="5" lines-valid="10"
            branches-covered="1" branches-valid="4" timestamp="123" version="1.0">
            <sources>
                <source>/src</source>
            </sources>
            <packages>
                <package name="pkg1" line-rate="0.5" branch-rate="0.4">
                    <classes>
                        <class name="Class1" filename="file1.py" line-rate="0.5" branch-rate="0.4">
                            <methods>
                                <method name="method1" signature="()V" line-rate="1.0" branch-rate="1.0" />
                            </methods>
                            <lines>
                                <line number="1" hits="1" branch="false" />
                                <line number="2" hits="0" branch="false" />
                                <line number="3" hits="1" branch="true" condition-coverage="50% (1/2)" />
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>
        """,
    )

    result = parser.parse_coverage_file(xml_path)

    assert result == {
        "format": "cobertura",
        "totals": {
            "lines_valid": 10,
            "lines_covered": 5,
            "line_rate": 0.5,
            "branches_valid": 4,
            "branches_covered": 1,
            "branch_rate": 0.25,
            "percent_covered": 50.0,
        },
        "packages": {
            "pkg1": {
                "line_rate": 0.5,
                "branch_rate": 0.4,
                "percent_covered": 50.0,
                "classes": {
                    "Class1": {
                        "filename": "file1.py",
                        "line_rate": 0.5,
                        "branch_rate": 0.4,
                        "percent_covered": 50.0,
                        "methods": {
                            "method1": {
                                "signature": "()V",
                                "line_rate": 1.0,
                                "branch_rate": 1.0,
                                "percent_covered": 100.0,
                            }
                        },
                    }
                },
            }
        },
        "files": {
            "file1.py": {
                "summary": {
                    "percent_covered": 50.0,
                    "line_rate": 0.5,
                    "branch_rate": 0.4,
                },
                "missing_lines": [2],
                "covered_lines": [1],
                "partial_lines": [3],
                "line_details": {
                    1: {
                        "hits": 1,
                        "branch": False,
                        "condition_coverage": "",
                    },
                    2: {
                        "hits": 0,
                        "branch": False,
                        "condition_coverage": "",
                    },
                    3: {
                        "hits": 1,
                        "branch": True,
                        "condition_coverage": "50% (1/2)",
                    },
                },
            }
        },
        "timestamp": "123",
        "version": "1.0",
        "source_paths": ["/src"],
    }


def test_parse_coverage_file_rejects_unknown_root(parser: CoberturaParser, tmp_path):
    xml_path = _write_xml(tmp_path, "<notcoverage></notcoverage>")

    assert parser.parse_coverage_file(xml_path) == {}


def test_convert_to_standard_format_translates_fields(parser: CoberturaParser):
    cobertura_data = {
        "format": "cobertura",
        "totals": {"percent_covered": 80.0},
        "files": {
            "file1.py": {
                "summary": {"percent_covered": 80.0, "line_rate": 0.8, "branch_rate": 0.6},
                "missing_lines": [10],
                "covered_lines": [9],
                "partial_lines": [],
                "line_details": {9: {"hits": 1, "branch": False, "condition_coverage": ""}},
            }
        },
        "timestamp": "456",
        "version": "2.0",
        "source_paths": ["/workspace"],
    }

    result = parser.convert_to_standard_format(cobertura_data)

    assert result == {
        "overall_coverage": 80.0,
        "file_coverage": {
            "file1.py": {
                "summary": {"percent_covered": 80.0, "line_rate": 0.8, "branch_rate": 0.6},
                "missing_lines": [10],
                "covered_lines": [9],
                "partial_lines": [],
                "line_details": {
                    9: {"hits": 1, "branch": False, "condition_coverage": ""}
                },
            }
        },
        "low_coverage_areas": [],
        "meets_threshold": False,
        "source_format": "cobertura",
        "metadata": {
            "timestamp": "456",
            "version": "2.0",
            "source_paths": ["/workspace"],
        },
    }


def test_convert_to_standard_format_handles_non_cobertura(parser: CoberturaParser):
    assert parser.convert_to_standard_format({"format": "other"}) == {}
