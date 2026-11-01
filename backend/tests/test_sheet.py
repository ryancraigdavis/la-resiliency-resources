import pytest

from la_resiliency.paths import default_paths
from la_resiliency.sheet import COLUMNS, parse_csv, parse_date, parse_flag, parse_phones, to_csv
from la_resiliency.store import load_catalog, parse_resources


def csv_text(rows: list[dict]) -> str:
    header = ",".join(COLUMNS)
    lines = [",".join(f'"{row.get(column, "")}"' for column in COLUMNS) for row in rows]
    return "\n".join([header, *lines])


@pytest.mark.parametrize(
    "cell,expected",
    [
        pytest.param("TRUE", True, id="sheets-checkbox"),
        pytest.param("yes", True, id="yes"),
        pytest.param("x", True, id="x"),
        pytest.param("FALSE", False, id="false"),
        pytest.param("", False, id="blank"),
    ],
)
def test_parse_flag(cell, expected):
    assert parse_flag(cell) is expected


@pytest.mark.parametrize(
    "cell,expected",
    [
        pytest.param("2026-06-30", "2026-06-30", id="iso"),
        pytest.param("6/30/2026", "2026-06-30", id="us-sheets-format"),
        pytest.param("6/30/26", "2026-06-30", id="short-year"),
        pytest.param("June", "June", id="unparseable-left-for-validation"),
    ],
)
def test_parse_date(cell, expected):
    assert parse_date(cell) == expected


def test_parse_phones():
    cell = "(800) 520-2356 | Chinese line | zh\n\n211"
    assert parse_phones(cell) == [
        {"number": "(800) 520-2356", "label": "Chinese line", "lang": "zh"},
        {"number": "211", "label": "", "lang": None},
    ]


@pytest.fixture
def sheet_row():
    return {
        "id": "sample",
        "active": "TRUE",
        "category": "food",
        "also_category": "benefits-health",
        "name": "Sample",
        "description": "Free food.",
        "lang_es": "TRUE",
        "lang_ko": "FALSE",
        "other_languages": "km, vi",
        "status_ok": "TRUE",
        "last_verified": "7/1/2026",
    }


def test_parse_csv_row(sheet_row):
    [resource] = parse_resources(parse_csv(csv_text([sheet_row])))
    assert resource.categories == ["food", "benefits-health"]
    assert resource.languages == ["es", "km", "vi"]
    assert (resource.status_ok, resource.audience, resource.url) == (True, "everyone", None)
    assert resource.last_verified.isoformat() == "2026-07-01"


def test_parse_csv_skips_blank_rows(sheet_row):
    assert len(parse_csv(csv_text([sheet_row, {}, {"notes": "x"}]))) == 1


def test_repository_catalog_round_trips_through_csv():
    resources = load_catalog(default_paths()).resources
    back = parse_resources(parse_csv(to_csv(resources)))

    def normalized(items):
        return [item.model_dump() | {"languages": sorted(item.languages)} for item in items]

    assert normalized(back) == normalized(resources)
