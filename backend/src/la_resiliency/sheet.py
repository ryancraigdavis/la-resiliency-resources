import contextlib
import csv
import io
from datetime import datetime

import httpx

from la_resiliency.languages import SHEET_LANGS
from la_resiliency.models import Resource

LANG_COLUMNS = tuple(f"lang_{code}" for code in SHEET_LANGS)
FLAG_COLUMNS = ("active", "status_ok", "multilingual", "urgent", "volatile")
TEXT_COLUMNS = (
    "id",
    "name",
    "url",
    "description",
    "who_its_for",
    "how_to_get_it",
    "tip",
    "audience",
    "cost",
)
COLUMNS = (
    ("id", "active", "category", "also_category", "name", "url", "phones")
    + ("description", "who_its_for", "how_to_get_it", "tip", "audience", "cost", "status_ok")
    + ("multilingual", *LANG_COLUMNS, "other_languages", "urgent", "volatile", "last_verified")
)
TRUTHY = {"true", "yes", "y", "x", "1"}
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y")


def fetch_csv(url: str) -> str:
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    return response.content.decode("utf-8-sig")


def split_list(cell: str) -> list[str]:
    return [part.strip() for part in cell.replace("\n", ",").split(",") if part.strip()]


def parse_flag(cell: str) -> bool:
    return cell.strip().lower() in TRUTHY


def try_date(cell: str, fmt: str) -> str | None:
    parsed = None
    with contextlib.suppress(ValueError):
        parsed = datetime.strptime(cell.strip(), fmt).date().isoformat()
    return parsed


def parse_date(cell: str) -> str:
    return next(filter(None, (try_date(cell, fmt) for fmt in DATE_FORMATS)), cell.strip())


def parse_phone(line: str) -> dict:
    number, label, lang = [*(part.strip() for part in line.split("|")), "", ""][:3]
    return {"number": number, "label": label, "lang": lang or None}


def parse_phones(cell: str) -> list[dict]:
    return [parse_phone(line) for line in cell.splitlines() if line.strip()]


def row_languages(row: dict) -> list[str]:
    checked = [code for code in SHEET_LANGS if parse_flag(row.get(f"lang_{code}", ""))]
    return checked + split_list(row.get("other_languages", ""))


def row_lists(cells: dict) -> dict:
    return {
        "categories": split_list(f"{cells.get('category', '')},{cells.get('also_category', '')}"),
        "phones": parse_phones(cells.get("phones", "")),
        "languages": row_languages(cells),
        "last_verified": parse_date(cells.get("last_verified", "")),
    }


def row_to_resource(row: dict) -> dict:
    cells = {key: (value or "") for key, value in row.items() if key}
    text = {column: cells.get(column, "").strip() for column in TEXT_COLUMNS}
    flags = {column: parse_flag(cells.get(column, "")) for column in FLAG_COLUMNS}
    optional = {"url": text["url"] or None, "audience": text["audience"] or "everyone"}
    return text | flags | optional | row_lists(cells)


def is_blank(row: dict) -> bool:
    return not ((row.get("id") or "").strip() or (row.get("name") or "").strip())


def parse_csv(text: str) -> list[dict]:
    rows = csv.DictReader(io.StringIO(text))
    return [row_to_resource(row) for row in rows if not is_blank(row)]


def format_phone(phone) -> str:
    return " | ".join(part for part in (phone.number, phone.label, phone.lang or "") if part)


def resource_lists(resource: Resource) -> dict:
    others = (code for code in resource.languages if code not in SHEET_LANGS)
    return {
        "category": resource.categories[0],
        "also_category": ", ".join(resource.categories[1:]),
        "phones": "\n".join(map(format_phone, resource.phones)),
        "other_languages": ", ".join(others),
        "last_verified": resource.last_verified.isoformat(),
    }


def resource_to_row(resource: Resource) -> dict:
    flags = {column: str(getattr(resource, column)).upper() for column in FLAG_COLUMNS}
    langs = {f"lang_{code}": str(code in resource.languages).upper() for code in SHEET_LANGS}
    text = {column: getattr(resource, column) or "" for column in TEXT_COLUMNS}
    return text | flags | langs | resource_lists(resource)


def to_csv(resources: list[Resource]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(map(resource_to_row, resources))
    return buffer.getvalue()
