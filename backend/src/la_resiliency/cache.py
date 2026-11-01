from dataclasses import dataclass

from la_resiliency.hashing import resource_hash, ui_hash
from la_resiliency.languages import LLM_LANGS, TRANSLATED_LANGS
from la_resiliency.paths import Paths
from la_resiliency.store import Catalog, read_json, write_json

Caches = dict[str, dict]


@dataclass(frozen=True)
class Job:
    kind: str
    key: str
    langs: tuple[str, ...]
    source_hash: str

    @property
    def custom_id(self) -> str:
        return f"{self.kind}__{self.key}"


def empty_cache() -> dict:
    return {"ui": {}, "resources": {}}


def load_caches(paths: Paths) -> Caches:
    return {lang: read_json(paths.cache_file(lang), None) or empty_cache() for lang in LLM_LANGS}


def sorted_cache(cache: dict) -> dict:
    return {"ui": cache["ui"], "resources": dict(sorted(cache["resources"].items()))}


def save_caches(paths: Paths, caches: Caches) -> None:
    for lang, cache in caches.items():
        write_json(paths.cache_file(lang), sorted_cache(cache))


def prune(caches: Caches, keep_ids: set[str]) -> Caches:
    return {
        lang: cache | {"resources": {k: v for k, v in cache["resources"].items() if k in keep_ids}}
        for lang, cache in caches.items()
    }


def cached_hash(caches: Caches, lang: str, section: str, key: str | None) -> str | None:
    entry = caches[lang][section].get(key, {}) if key else caches[lang][section]
    return entry.get("source_hash")


def stale_langs(caches: Caches, rid: str, current: str, langs) -> tuple[str, ...]:
    return tuple(code for code in langs if cached_hash(caches, code, "resources", rid) != current)


def resource_job(resource, caches: Caches, langs) -> Job:
    current = resource_hash(resource)
    return Job("resource", resource.id, stale_langs(caches, resource.id, current, langs), current)


def resource_jobs(catalog: Catalog, caches: Caches, langs=LLM_LANGS) -> list[Job]:
    jobs = (resource_job(r, caches, langs) for r in catalog.resources if r.active)
    return [job for job in jobs if job.langs]


def ui_jobs(catalog: Catalog, caches: Caches, langs=TRANSLATED_LANGS) -> list[Job]:
    current = ui_hash(catalog.ui, catalog.categories)
    return [
        Job("ui", lang, (lang,), current)
        for lang in langs
        if lang in TRANSLATED_LANGS and cached_hash(caches, lang, "ui", None) != current
    ]
