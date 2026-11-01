import json

from la_resiliency.hashing import resource_source, ui_source
from la_resiliency.languages import BY_CODE
from la_resiliency.models import Resource
from la_resiliency.store import Catalog

TEXT_FIELDS = ("headline", "description", "who_its_for", "how_to_get_it", "tip")
LIST_FIELDS = ("phone_labels", "search_terms")

RESOURCE_SYSTEM = """\
You translate entries for a free community resource directory in Los Angeles. People use it when \
they need food, housing, immigration help, health care, or work. Many are under stress, new to \
the United States, or not strong readers, and they will act on what you write. Accuracy and \
plain words matter more than style.

You receive one resource in English and a list of target languages. For each language return:

headline: at most 8 words saying what the resource helps with, in plain words, for example \
"Free legal help if you are being evicted". Do not repeat the organization's name.

description, who_its_for, how_to_get_it, tip: faithful translations of the English fields, in \
simple, warm, everyday words (about a 6th-grade reading level). Keep every fact exactly: \
numbers, dollar amounts, ages, dates, deadlines, hours, and conditions. Do not add facts, \
advice, or promises that are not in the English. If an English field is empty, return "".

phone_labels: translate each phone label, in the same order and the same count. An empty label \
stays "".

search_terms: 15 to 25 words or short phrases a person needing this resource might type into a \
search box in that language. Mix everyday words, informal or slang terms, common misspellings \
or missing accents, and short descriptions of the situation that leads someone here. For an \
eviction resource in Spanish that could be "desalojo", "me quieren sacar de mi casa", "renta", \
"casero", "desalojo corte". Include the names people commonly use for programs (for example \
"food stamps", "estampillas de comida"). No phone numbers, web addresses, or the organization's \
own name.

For "en", return only headline and search_terms; return "" for the other text fields and an \
empty list for phone_labels.

Keep these exactly as written in English, never translated or transliterated: organization, \
program, and website names, and the terms CalFresh, CFAP, CAPI, WIC, Medi-Cal, SSI, SNAP, EBT, \
DPSS, LAUSD, ICE, BenefitsCal, LA4Families.org, and 211. The first time a program name appears \
in a field you may add a very short explanation in parentheses, for example \
"CalFresh (ayuda para comprar comida)".

For Church terms, use the wording The Church of Jesus Christ of Latter-day Saints uses in that \
language, including its official name where one exists (for example bishop is "obispo" in \
Spanish, "감독" in Korean, and "主教" in Chinese).

Never write phone numbers or web addresses into any field.\
"""

UI_SYSTEM = """\
You translate the interface text of a free community resource website in Los Angeles. Readers \
may be under stress, new to the United States, or not strong readers. Use short, simple, warm, \
everyday words. Button and label text must stay short.

Keep every {placeholder} exactly as written, including the braces. Keep "211" as written. For \
category labels and blurbs, translate the meaning naturally rather than word for word.

Translate site_name by meaning, not word for word: a short, natural name of at most 6 words that \
tells a reader at a glance this site lists free help and resources in Los Angeles. Write Los \
Angeles the way that language usually writes it.\
"""


def string_schema() -> dict:
    return {"type": "string"}


def strict_object(properties: dict) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def entry_schema() -> dict:
    texts = {field: string_schema() for field in TEXT_FIELDS}
    lists = {field: {"type": "array", "items": string_schema()} for field in LIST_FIELDS}
    return strict_object(texts | lists)


def resource_schema(langs: tuple[str, ...]) -> dict:
    return strict_object({lang: entry_schema() for lang in langs})


def ui_schema(catalog: Catalog) -> dict:
    strings = {key: string_schema() for key in catalog.ui}
    pair = strict_object({"label": string_schema(), "blurb": string_schema()})
    categories = {category.id: pair for category in catalog.categories}
    return strict_object(
        {"strings": strict_object(strings), "categories": strict_object(categories)}
    )


def language_list(langs: tuple[str, ...]) -> list[dict]:
    return [{"code": lang, "language": BY_CODE[lang].prompt} for lang in langs]


def resource_prompt(resource: Resource, catalog: Catalog, langs: tuple[str, ...]) -> str:
    topics = {c.id: c.label for c in catalog.categories}
    context = {
        "topics": [topics[c] for c in resource.categories if c in topics],
        "audience": resource.audience,
    }
    payload = {
        "languages": language_list(langs),
        "resource": resource_source(resource),
        "context": context,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def ui_prompt(catalog: Catalog, lang: str) -> str:
    payload = {"language": language_list((lang,))[0], **ui_source(catalog.ui, catalog.categories)}
    return json.dumps(payload, ensure_ascii=False, indent=2)
