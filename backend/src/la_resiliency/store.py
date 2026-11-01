import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import TypeAdapter, ValidationError

from la_resiliency.models import Category, Resource
from la_resiliency.paths import Paths

RESOURCES = TypeAdapter(list[Resource])
CATEGORIES = TypeAdapter(list[Category])
UI_STRINGS = TypeAdapter(dict[str, str])

RESOURCES_HEADER = (
    "# English source of truth, synced from the co-chairs' Google Sheet by `la-resiliency pull`.\n"
    "# Edit the Sheet: this file is overwritten on the next sync.\n\n"
)


class DataError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class Catalog:
    resources: list[Resource]
    categories: list[Category]
    ui: dict[str, str]


def read_yaml(path: Path, default=None):
    return yaml.safe_load(path.read_text("utf-8")) if path.exists() else default


def read_json(path: Path, default=None):
    return json.loads(path.read_text("utf-8")) if path.exists() else default


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")


def write_json(path: Path, data) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def describe_error(error: dict, raw: list) -> str:
    index, *field = error["loc"]
    name = raw[index].get("id") or f"entry #{index + 1}"
    return f"{name}: {'.'.join(map(str, field)) or 'entry'}: {error['msg']}"


def parse_resources(raw: list[dict]) -> list[Resource]:
    try:
        return RESOURCES.validate_python(raw)
    except ValidationError as exc:
        raise DataError([describe_error(error, raw) for error in exc.errors()]) from exc


def catalog_problems(resources: list[Resource], categories: list[Category]) -> list[str]:
    known = {category.id for category in categories}
    unknown = [
        f"{resource.id}: unknown category '{category}'"
        for resource in resources
        for category in resource.categories
        if category not in known
    ]
    counts = Counter(resource.id for resource in resources)
    duplicates = [f"{rid}: id is used {count} times" for rid, count in counts.items() if count > 1]
    return unknown + duplicates


def check_catalog(catalog: Catalog) -> Catalog:
    problems = catalog_problems(catalog.resources, catalog.categories)
    if problems:
        raise DataError(problems)
    return catalog


def load_catalog(paths: Paths) -> Catalog:
    return check_catalog(
        Catalog(
            resources=parse_resources(read_yaml(paths.resources, [])),
            categories=CATEGORIES.validate_python(read_yaml(paths.categories, [])),
            ui=UI_STRINGS.validate_python(read_yaml(paths.ui, {})),
        )
    )


def resource_yaml(resource: Resource) -> str:
    data = resource.model_dump(exclude_defaults=True)
    return yaml.safe_dump(
        [data], allow_unicode=True, sort_keys=False, width=1000, default_flow_style=None
    )


def dump_resources(resources: list[Resource], path: Path) -> None:
    write_text(path, RESOURCES_HEADER + "\n".join(map(resource_yaml, resources)))
