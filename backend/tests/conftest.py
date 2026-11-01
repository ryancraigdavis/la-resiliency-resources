import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from la_resiliency.paths import REPO_ROOT, Paths
from la_resiliency.store import load_catalog

SAMPLE_RESOURCES = [
    {
        "id": "food-bank",
        "categories": ["food"],
        "name": "Sample Food Bank",
        "url": "https://example.org/food",
        "phones": [{"number": "(800) 555-0100", "label": "Main line"}],
        "description": "Free groceries every week.",
        "who_its_for": "Anyone in LA County.",
        "last_verified": "2026-06-30",
    },
    {
        "id": "tenant-help",
        "categories": ["housing", "immigration-legal"],
        "name": "Tenant Help",
        "description": "Legal help if you are being evicted.",
        "tip": "Respond within 5 days.",
        "urgent": True,
        "last_verified": "2026-07-15",
    },
    {
        "id": "retired-program",
        "categories": ["jobs"],
        "name": "Retired Program",
        "description": "No longer offered.",
        "active": False,
        "last_verified": "2025-01-01",
    },
]


@pytest.fixture
def sample_resources() -> list[dict]:
    return SAMPLE_RESOURCES


@pytest.fixture
def paths(tmp_path: Path) -> Paths:
    data = tmp_path / "data"
    data.mkdir()
    for name in ("categories.yaml", "ui.yaml"):
        shutil.copy(REPO_ROOT / "data" / name, data / name)
    (data / "resources.yaml").write_text(yaml.safe_dump(SAMPLE_RESOURCES), "utf-8")
    return Paths(tmp_path)


@pytest.fixture
def catalog(paths):
    return load_catalog(paths)


def fake_usage():
    return SimpleNamespace(
        input_tokens=1000,
        output_tokens=500,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=200,
    )


def make_message(payload: dict, stop_reason: str = "end_turn"):
    text = SimpleNamespace(type="text", text=json.dumps(payload, ensure_ascii=False))
    return SimpleNamespace(stop_reason=stop_reason, content=[text], usage=fake_usage())


def fake_entry(lang: str, source: dict) -> dict:
    return {
        "headline": f"[{lang}] headline",
        "description": f"[{lang}] {source['description']}",
        "who_its_for": f"[{lang}] {source['who_its_for']}" if source["who_its_for"] else "",
        "how_to_get_it": "",
        "tip": f"[{lang}] {source['tip']}" if source["tip"] else "",
        "phone_labels": [f"[{lang}] {label}" for label in source["phone_labels"]],
        "search_terms": [f"{lang} word", f"{lang} word", " "],
    }


def fake_ui(content: dict) -> dict:
    strings = {key: f"~{value}" for key, value in content["strings"].items()}
    return {"strings": strings, "categories": content["categories"]}


def fake_payload(content_text: str) -> dict:
    content = json.loads(content_text)
    langs = [item["code"] for item in content.get("languages", [])]
    resource = {lang: fake_entry(lang, content["resource"]) for lang in langs}
    return resource if langs else fake_ui(content)


def fake_response(params: dict):
    return make_message(fake_payload(params["messages"][0]["content"]))


def cli_process(stdout: str, returncode: int = 0, stderr: str = ""):
    return subprocess.CompletedProcess(["claude"], returncode, stdout=stdout, stderr=stderr)


def fake_cli_run(args, input, **kwargs):
    result = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "structured_output": fake_payload(input),
        "usage": {"input_tokens": 900, "output_tokens": 300},
    }
    return cli_process(json.dumps(result, ensure_ascii=False))


@pytest.fixture
def fake_client(mocker):
    client = mocker.Mock()
    client.messages.create.side_effect = lambda **params: fake_response(params)
    return client


@pytest.fixture
def message_factory():
    return make_message


@pytest.fixture
def responder():
    return fake_response


@pytest.fixture
def fake_claude_code(mocker):
    mocker.patch("la_resiliency.runners.shutil.which", return_value="/usr/bin/claude")
    return mocker.patch("la_resiliency.runners.subprocess.run", side_effect=fake_cli_run)


@pytest.fixture
def process_factory():
    return cli_process
