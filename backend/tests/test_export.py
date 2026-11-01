import pytest
import yaml

from la_resiliency.cache import empty_cache, resource_jobs, ui_jobs
from la_resiliency.export import both_scripts, export_site, site_caches, site_document
from la_resiliency.languages import LLM_LANGS, SITE_LANGS
from la_resiliency.store import read_json
from la_resiliency.translate import translate


@pytest.fixture
def caches():
    return {lang: empty_cache() for lang in LLM_LANGS}


@pytest.fixture
def translated(fake_client, catalog, caches):
    jobs = ui_jobs(catalog, caches) + resource_jobs(catalog, caches)
    translate(fake_client, catalog, caches, jobs, "direct")
    return caches


def document(catalog, caches, lang, overrides=None):
    all_overrides = {code: {} for code in SITE_LANGS} | (overrides or {})
    return site_document(catalog, lang, site_caches(caches), all_overrides)


def resource(doc, rid):
    return next(item for item in doc["resources"] if item["id"] == rid)


def test_untranslated_falls_back_to_english(catalog, caches):
    doc = document(catalog, caches, "fa")
    food = resource(doc, "food-bank")
    assert (doc["dir"], doc["machine_translated"]) == ("rtl", False)
    assert food["description"] == "Free groceries every week."
    assert food["machine_translated"] is False
    assert food["text_lang"] == "en"


def test_translated_text_is_used(catalog, translated):
    food = resource(document(catalog, translated, "es"), "food-bank")
    assert food["description"] == "[es] Free groceries every week."
    assert food["headline"] == "[es] headline"
    assert food["phones"] == [
        {"number": "(800) 555-0100", "tel": "+18005550100", "label": "[es] Main line", "lang": None}
    ]
    assert food["machine_translated"] is True
    assert food["text_lang"] == "es"


def test_empty_translated_field_keeps_empty_source(catalog, translated):
    assert resource(document(catalog, translated, "es"), "tenant-help")["who_its_for"] == ""


def test_english_gets_generated_headline(catalog, translated):
    food = resource(document(catalog, translated, "en"), "food-bank")
    assert (food["headline"], food["description"]) == (
        "[en] headline",
        "Free groceries every week.",
    )


def test_stale_translation_is_not_shown(catalog, translated):
    catalog.resources[0].description = "Groceries on Saturdays only."
    food = resource(document(catalog, translated, "ko"), "food-bank")
    assert food["description"] == "Groceries on Saturdays only."


def test_overrides_win_and_count_as_reviewed(catalog, translated):
    overrides = {"es": {"resources": {"food-bank": {"headline": "Comida gratis"}}}}
    food = resource(document(catalog, translated, "es", overrides), "food-bank")
    assert (food["headline"], food["machine_translated"]) == ("Comida gratis", False)


def test_reviewed_list_clears_machine_flag(catalog, translated):
    food = resource(
        document(catalog, translated, "tr", {"tr": {"reviewed": ["food-bank"]}}), "food-bank"
    )
    assert food["machine_translated"] is False


def test_inactive_resources_are_hidden(catalog, caches):
    ids = [item["id"] for item in document(catalog, caches, "en")["resources"]]
    assert ids == ["food-bank", "tenant-help"]


def test_categories_are_translated_and_counted(catalog, translated):
    doc = document(catalog, translated, "es")
    housing = next(c for c in doc["categories"] if c["id"] == "housing")
    assert (housing["count"], doc["ui"]["search_button"]) == (1, "~Search")


def test_traditional_chinese_uses_modern_standard_forms(catalog, caches):
    caches["zh-hans"]["resources"]["food-bank"] = {"source_hash": "x", "tip": "因为身份，这里"}
    assert site_caches(caches)["zh-hant"]["resources"]["food-bank"]["tip"] == "因為身份，這裡"


def test_traditional_chinese_is_derived(catalog, caches):
    caches["zh-hans"]["resources"]["food-bank"] = {"source_hash": "x", "search_terms": ["免费食物"]}
    derived = site_caches(caches)
    assert derived["zh-hant"]["resources"]["food-bank"]["search_terms"] == ["免費食物", "免费食物"]


@pytest.mark.parametrize(
    "terms,expected",
    [
        pytest.param(["房租"], ["房租"], id="same-in-both"),
        pytest.param(["律师"], ["律师", "律師"], id="simplified-adds-traditional"),
        pytest.param(["律師"], ["律師", "律师"], id="traditional-adds-simplified"),
    ],
)
def test_both_scripts(terms, expected):
    assert both_scripts(terms) == expected


def test_export_writes_every_language(paths, catalog, translated):
    paths.overrides.mkdir(parents=True)
    paths.override_file("ko").write_text(yaml.safe_dump({"ui": {"call": "전화하기"}}), "utf-8")
    export_site(paths, catalog, translated)
    assert read_json(paths.site_data / "ko.json")["ui"]["call"] == "전화하기"
    meta = read_json(paths.site_data / "meta.json")
    assert [lang["code"] for lang in meta["languages"]] == list(SITE_LANGS)
    assert meta["topics"][0] == "detained"
