from opencc import OpenCC

from la_resiliency.cache import Caches
from la_resiliency.hashing import resource_hash, ui_hash
from la_resiliency.languages import BY_CODE, LANGUAGES, SITE_LANGS
from la_resiliency.models import Category, Resource
from la_resiliency.paths import Paths
from la_resiliency.store import Catalog, read_yaml, write_json

TO_TRADITIONAL = OpenCC("s2tw")
TO_SIMPLIFIED = OpenCC("t2s")
SOURCE_FIELDS = ("description", "who_its_for", "how_to_get_it", "tip")
CHINESE = ("zh-hans", "zh-hant")


def convert(value, converter: OpenCC):
    converters = {
        str: converter.convert,
        list: lambda items: [convert(item, converter) for item in items],
        dict: lambda mapping: {key: convert(item, converter) for key, item in mapping.items()},
    }
    return converters.get(type(value), lambda other: other)(value)


def both_scripts(terms: list[str]) -> list[str]:
    variants = [*terms, *map(TO_TRADITIONAL.convert, terms), *map(TO_SIMPLIFIED.convert, terms)]
    return list(dict.fromkeys(variants))


def with_both_scripts(cache: dict) -> dict:
    resources = {
        rid: entry | {"search_terms": both_scripts(entry.get("search_terms", []))}
        for rid, entry in cache["resources"].items()
    }
    return cache | {"resources": resources}


def site_caches(caches: Caches) -> Caches:
    derived = {"zh-hant": convert(caches["zh-hans"], TO_TRADITIONAL)}
    merged = caches | derived
    return merged | {lang: with_both_scripts(merged[lang]) for lang in CHINESE}


def load_overrides(paths: Paths) -> dict[str, dict]:
    return {lang: read_yaml(paths.override_file(lang), None) or {} for lang in SITE_LANGS}


def fresh_entry(cache: dict, resource: Resource) -> dict:
    entry = cache["resources"].get(resource.id, {})
    return entry if entry.get("source_hash") == resource_hash(resource) else {}


def phone_records(resource: Resource, labels: list[str]) -> list[dict]:
    return [
        {"number": phone.number, "tel": phone.tel, "label": label, "lang": phone.lang}
        for phone, label in zip(resource.phones, labels, strict=True)
    ]


def resource_record(
    resource: Resource, lang: str, cache: dict, en_cache: dict, override: dict
) -> dict:
    entry = fresh_entry(cache, resource)
    english = fresh_entry(en_cache, resource)
    edits = override.get("resources", {}).get(resource.id, {})
    reviewed = resource.id in override.get("reviewed", []) or bool(edits)
    source_labels = [phone.label for phone in resource.phones]
    labels = edits.get("phone_labels") or entry.get("phone_labels") or source_labels
    text = {field: entry.get(field) or getattr(resource, field) for field in SOURCE_FIELDS}
    translated = bool(entry.get("description") or edits.get("description"))
    return {
        "id": resource.id,
        "categories": resource.categories,
        "name": resource.name,
        "url": resource.url,
        "headline": entry.get("headline") or english.get("headline", ""),
        **text,
        "phones": phone_records(resource, labels),
        "search_terms": entry.get("search_terms", []),
        "audience": resource.audience,
        "status_ok": resource.status_ok,
        "cost": resource.cost,
        "languages": resource.languages,
        "multilingual": resource.multilingual,
        "urgent": resource.urgent,
        "volatile": resource.volatile,
        "last_verified": resource.last_verified.isoformat(),
        "text_lang": lang if translated or lang == "en" else "en",
        "machine_translated": bool(entry.get("description")) and not reviewed,
    } | {key: value for key, value in edits.items() if key != "phone_labels"}


def fresh_ui(cache: dict, catalog: Catalog) -> dict:
    ui = cache["ui"]
    return ui if ui.get("source_hash") == ui_hash(catalog.ui, catalog.categories) else {}


def category_record(category: Category, ui: dict, override: dict, resources) -> dict:
    translated = ui.get("categories", {}).get(category.id, {})
    edits = override.get("categories", {}).get(category.id, {})
    return (
        {
            "id": category.id,
            "icon": category.icon,
            "urgent": category.urgent,
            "label": category.label,
            "blurb": category.blurb,
            "count": sum(category.id in resource.categories for resource in resources),
        }
        | translated
        | edits
    )


def active(catalog: Catalog) -> list[Resource]:
    return [resource for resource in catalog.resources if resource.active]


def site_document(catalog: Catalog, lang: str, caches: Caches, overrides: dict) -> dict:
    cache, override = caches[lang], overrides[lang]
    ui = fresh_ui(cache, catalog)
    resources = active(catalog)
    return {
        "lang": lang,
        "dir": BY_CODE[lang].dir,
        "updated": max(r.last_verified for r in resources).isoformat(),
        "machine_translated": bool(ui) and not override.get("ui_reviewed", False),
        "ui": catalog.ui | ui.get("strings", {}) | override.get("ui", {}),
        "categories": [category_record(c, ui, override, resources) for c in catalog.categories],
        "resources": [resource_record(r, lang, cache, caches["en"], override) for r in resources],
    }


def meta_document(catalog: Catalog) -> dict:
    languages = [{"code": lang.code, "native": lang.native, "dir": lang.dir} for lang in LANGUAGES]
    topics = [category.id for category in catalog.categories]
    return {"default": "en", "languages": languages, "topics": topics}


def export_site(paths: Paths, catalog: Catalog, caches: Caches) -> list[str]:
    all_caches = site_caches(caches)
    overrides = load_overrides(paths)
    for lang in SITE_LANGS:
        write_json(
            paths.site_data / f"{lang}.json", site_document(catalog, lang, all_caches, overrides)
        )
    write_json(paths.site_data / "meta.json", meta_document(catalog))
    return list(SITE_LANGS)
