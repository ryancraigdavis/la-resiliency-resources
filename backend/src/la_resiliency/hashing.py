import hashlib
import json

from la_resiliency.models import Category, Resource

PROMPT_VERSION = 1


def digest(payload) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def resource_source(resource: Resource) -> dict:
    return {
        "name": resource.name,
        "description": resource.description,
        "who_its_for": resource.who_its_for,
        "how_to_get_it": resource.how_to_get_it,
        "tip": resource.tip,
        "phone_labels": [phone.label for phone in resource.phones],
    }


def ui_source(ui: dict[str, str], categories: list[Category]) -> dict:
    labels = {c.id: {"label": c.label, "blurb": c.blurb} for c in categories}
    return {"strings": ui, "categories": labels}


def resource_hash(resource: Resource) -> str:
    return digest({"v": PROMPT_VERSION, **resource_source(resource)})


def ui_hash(ui: dict[str, str], categories: list[Category]) -> str:
    return digest({"v": PROMPT_VERSION, **ui_source(ui, categories)})
