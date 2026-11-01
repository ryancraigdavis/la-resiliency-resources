import pytest
import yaml

from la_resiliency.paths import default_paths
from la_resiliency.store import DataError, dump_resources, load_catalog, parse_resources


def test_repository_data_is_valid():
    catalog = load_catalog(default_paths())
    assert len(catalog.resources) > 80


def test_repository_ui_placeholders_are_known():
    ui = load_catalog(default_paths()).ui
    assert "{language}" in ui["help_in_language"]


@pytest.fixture
def write_resources(paths):
    def write(entries):
        paths.resources.write_text(yaml.safe_dump(entries), "utf-8")
        return paths

    return write


@pytest.mark.parametrize(
    "mutate,message",
    [
        pytest.param(
            lambda e: e[0].update(categories=["nope"]), "unknown category 'nope'", id="cat"
        ),
        pytest.param(lambda e: e[1].update(id="food-bank"), "id is used 2 times", id="dup-id"),
        pytest.param(lambda e: e[0].update(url="example.org"), "food-bank: url", id="bad-url"),
    ],
)
def test_load_catalog_reports_problems(write_resources, sample_resources, mutate, message):
    entries = [dict(entry) for entry in sample_resources]
    mutate(entries)
    with pytest.raises(DataError) as error:
        load_catalog(write_resources(entries))
    assert any(message in problem for problem in error.value.problems)


def test_dump_round_trips(paths, catalog):
    dump_resources(catalog.resources, paths.resources)
    assert load_catalog(paths).resources == catalog.resources


def test_dump_omits_defaults(paths, catalog):
    dump_resources(catalog.resources, paths.resources)
    text = paths.resources.read_text("utf-8")
    assert "status_ok" not in text
    assert text.startswith("# English source of truth")


def test_parse_resources_names_entry_without_id():
    with pytest.raises(DataError) as error:
        parse_resources([{"name": "No id"}])
    assert error.value.problems[0].startswith("entry #1: id:")
