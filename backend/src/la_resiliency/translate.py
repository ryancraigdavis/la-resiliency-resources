import json
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict

from la_resiliency.cache import Caches, Job
from la_resiliency.hashing import resource_source
from la_resiliency.prompts import (
    RESOURCE_SYSTEM,
    UI_SYSTEM,
    resource_prompt,
    resource_schema,
    ui_prompt,
    ui_schema,
)
from la_resiliency.runners import RUNNERS, USAGE_KEYS, Outcome, TranslationError
from la_resiliency.store import Catalog

MODEL = "claude-opus-5"
MAX_TOKENS = 16000
EFFORT = "medium"
MODES = tuple(RUNNERS)
PRICES_PER_MTOK = {
    "input_tokens": 5.0,
    "output_tokens": 25.0,
    "cache_creation_input_tokens": 6.25,
    "cache_read_input_tokens": 0.5,
}
MODE_DISCOUNT = {"claude-code": 0.0, "direct": 1.0, "batch": 0.5}
EN_FIELDS = ("headline", "search_terms")
MAX_SEARCH_TERMS = 30
PHONE_LIKE = re.compile(r"\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}")
WEB_ADDRESS = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
PLACEHOLDER = re.compile(r"\{\w+\}")

__all__ = ["MODES", "Report", "TranslationError", "translate"]


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    headline: str
    description: str
    who_its_for: str
    how_to_get_it: str
    tip: str
    phone_labels: list[str]
    search_terms: list[str]


class CategoryText(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    blurb: str


class UiText(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strings: dict[str, str]
    categories: dict[str, CategoryText]


@dataclass
class Report:
    mode: str
    translated: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    usage: dict[str, int] = field(default_factory=lambda: dict.fromkeys(USAGE_KEYS, 0))

    @property
    def api_equivalent_cost(self) -> float:
        return sum(self.usage[key] * price for key, price in PRICES_PER_MTOK.items()) / 1_000_000

    @property
    def cost(self) -> float:
        return self.api_equivalent_cost * MODE_DISCOUNT[self.mode]

    @property
    def cost_text(self) -> str:
        covered = "covered by your Claude plan"
        return covered if self.mode == "claude-code" else f"about ${self.cost:.2f}"


def base_params(system: str, content: str, schema: dict) -> dict:
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": content}],
        "output_config": {"effort": EFFORT, "format": {"type": "json_schema", "schema": schema}},
    }


def resource_request(job: Job, catalog: Catalog) -> dict:
    resource = next(r for r in catalog.resources if r.id == job.key)
    content = resource_prompt(resource, catalog, job.langs)
    return base_params(RESOURCE_SYSTEM, content, resource_schema(job.langs))


def ui_request(job: Job, catalog: Catalog) -> dict:
    return base_params(UI_SYSTEM, ui_prompt(catalog, job.key), ui_schema(catalog))


REQUEST_BUILDERS = {"resource": resource_request, "ui": ui_request}


def request_params(job: Job, catalog: Catalog) -> dict:
    return REQUEST_BUILDERS[job.kind](job, catalog)


def ascii_digits(text: str) -> str:
    return "".join(str(unicodedata.digit(char)) for char in text if char.isdigit())


def phone_numbers(text: str) -> set[str]:
    return set(map(ascii_digits, PHONE_LIKE.findall(text)))


def web_addresses(text: str) -> set[str]:
    return set(WEB_ADDRESS.findall(text))


def all_text(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def new_contacts(source: dict, translated) -> set[str]:
    before, after = all_text(source), all_text(translated)
    phones = phone_numbers(after) - phone_numbers(before)
    return phones | (web_addresses(after) - web_addresses(before))


def clean_terms(terms: list[str]) -> list[str]:
    stripped = (term.strip() for term in terms)
    unique = dict.fromkeys(t for t in stripped if t and not new_contacts({}, t) and len(t) <= 60)
    return list(unique)[:MAX_SEARCH_TERMS]


def entry_problems(lang: str, entry: Entry, source: dict) -> list[str]:
    expected = len(source["phone_labels"])
    invented = new_contacts(source, entry.model_dump(exclude={"search_terms"}))
    checks = {
        f"{lang}: expected {expected} phone labels": lang != "en"
        and len(entry.phone_labels) != expected,
        f"{lang}: added phone numbers or web addresses {sorted(invented)}": bool(invented),
    }
    return [message for message, failed in checks.items() if failed]


def stored_entry(lang: str, entry: Entry, source_hash: str) -> dict:
    data = entry.model_dump() | {"search_terms": clean_terms(entry.search_terms)}
    kept = {key: data[key] for key in (EN_FIELDS if lang == "en" else data)}
    return {"source_hash": source_hash, **kept}


def merge_resource(job: Job, payload: dict, catalog: Catalog, caches: Caches) -> None:
    resource = next(r for r in catalog.resources if r.id == job.key)
    source = resource_source(resource)
    entries = {lang: Entry.model_validate(payload[lang]) for lang in job.langs}
    problems = [p for lang, entry in entries.items() for p in entry_problems(lang, entry, source)]
    if problems:
        raise TranslationError("; ".join(problems))
    for lang, entry in entries.items():
        caches[lang]["resources"][job.key] = stored_entry(lang, entry, job.source_hash)


def placeholder_problems(source: dict[str, str], translated: dict[str, str]) -> list[str]:
    return [
        f"{key}: placeholders changed"
        for key, text in source.items()
        if set(PLACEHOLDER.findall(text)) != set(PLACEHOLDER.findall(translated.get(key, "")))
    ]


def merge_ui(job: Job, payload: dict, catalog: Catalog, caches: Caches) -> None:
    text = UiText.model_validate(payload)
    problems = placeholder_problems(catalog.ui, text.strings)
    if problems:
        raise TranslationError("; ".join(problems))
    caches[job.key]["ui"] = {"source_hash": job.source_hash, **text.model_dump()}


MERGERS = {"resource": merge_resource, "ui": merge_ui}


def add_usage(report: Report, outcome: Outcome) -> None:
    for key in report.usage:
        report.usage[key] += outcome.usage.get(key, 0)


def raise_if_error(outcome) -> None:
    if isinstance(outcome, BaseException):
        raise outcome


def apply_outcome(job: Job, outcome, catalog: Catalog, caches: Caches, report: Report) -> None:
    try:
        raise_if_error(outcome)
        add_usage(report, outcome)
        MERGERS[job.kind](job, outcome.payload, catalog, caches)
        report.translated.append(job.custom_id)
    except Exception as exc:  # recorded and retried on the next run
        report.failed[job.custom_id] = f"{type(exc).__name__}: {exc}"


def ignore_progress(custom_id: str, report: Report) -> None:
    return None


def translate(
    client,
    catalog: Catalog,
    caches: Caches,
    jobs: list[Job],
    mode: str,
    *,
    on_result: Callable[[str, Report], None] = ignore_progress,
) -> Report:
    report = Report(mode)
    by_id = {job.custom_id: job for job in jobs}
    requests = {cid: request_params(job, catalog) for cid, job in by_id.items()}
    results = RUNNERS[mode](client, requests) if requests else iter(())
    for custom_id, outcome in results:
        apply_outcome(by_id[custom_id], outcome, catalog, caches, report)
        on_result(custom_id, report)
    missing = [job for cid, job in by_id.items() if cid not in report.translated + [*report.failed]]
    for job in missing:
        apply_outcome(job, TranslationError("no result returned"), catalog, caches, report)
    return report
