import pytest

from la_resiliency.cache import empty_cache, load_caches, prune, resource_jobs, save_caches, ui_jobs
from la_resiliency.hashing import resource_hash, ui_hash
from la_resiliency.languages import LLM_LANGS, TRANSLATED_LANGS


@pytest.fixture
def caches():
    return {lang: empty_cache() for lang in LLM_LANGS}


def mark_fresh(caches, catalog, langs=LLM_LANGS):
    for resource in catalog.resources:
        for lang in langs:
            caches[lang]["resources"][resource.id] = {"source_hash": resource_hash(resource)}


def test_everything_active_is_stale_at_first(catalog, caches):
    jobs = resource_jobs(catalog, caches)
    assert [job.key for job in jobs] == ["food-bank", "tenant-help"]
    assert all(job.langs == LLM_LANGS for job in jobs)


def test_fresh_entries_need_no_jobs(catalog, caches):
    mark_fresh(caches, catalog)
    assert resource_jobs(catalog, caches) == []


def test_only_missing_languages_are_planned(catalog, caches):
    mark_fresh(caches, catalog, langs=("en", "es"))
    assert {job.langs for job in resource_jobs(catalog, caches)} == {("ko", "zh-hans", "fa", "tr")}


def test_editing_text_makes_resource_stale(catalog, caches):
    mark_fresh(caches, catalog)
    catalog.resources[0].description = "Free groceries on Saturdays."
    assert [job.key for job in resource_jobs(catalog, caches)] == ["food-bank"]


def test_editing_flags_does_not_retranslate(catalog, caches):
    mark_fresh(caches, catalog)
    catalog.resources[0].urgent = True
    assert resource_jobs(catalog, caches) == []


@pytest.mark.parametrize(
    "fresh_langs,expected",
    [
        pytest.param((), TRANSLATED_LANGS, id="all-stale"),
        pytest.param(("es", "ko"), ("zh-hans", "fa", "tr"), id="some-fresh"),
    ],
)
def test_ui_jobs(catalog, caches, fresh_langs, expected):
    for lang in fresh_langs:
        caches[lang]["ui"] = {"source_hash": ui_hash(catalog.ui, catalog.categories)}
    assert tuple(job.key for job in ui_jobs(catalog, caches)) == expected


def test_custom_id_is_batch_safe(catalog, caches):
    job = resource_jobs(catalog, caches)[0]
    assert job.custom_id == "resource__food-bank"


def test_prune_and_save_round_trip(paths, catalog, caches):
    mark_fresh(caches, catalog)
    caches["es"]["resources"]["deleted-thing"] = {"source_hash": "x"}
    save_caches(paths, prune(caches, {"food-bank", "tenant-help"}))
    assert sorted(load_caches(paths)["es"]["resources"]) == ["food-bank", "tenant-help"]
