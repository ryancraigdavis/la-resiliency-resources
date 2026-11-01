import json
from types import SimpleNamespace

import pytest

from la_resiliency.cache import empty_cache, resource_jobs, ui_jobs
from la_resiliency.hashing import resource_hash
from la_resiliency.languages import LLM_LANGS
from la_resiliency.runners import run_batch
from la_resiliency.store import DataError
from la_resiliency.translate import Report, clean_terms, new_contacts, translate


@pytest.fixture
def caches():
    return {lang: empty_cache() for lang in LLM_LANGS}


@pytest.fixture
def jobs(catalog, caches):
    return resource_jobs(catalog, caches)


def test_translate_fills_every_language(fake_client, catalog, caches, jobs):
    report = translate(fake_client, catalog, caches, jobs, "direct")
    entry = caches["ko"]["resources"]["food-bank"]
    assert report.failed == {}
    assert entry["description"] == "[ko] Free groceries every week."
    assert entry["phone_labels"] == ["[ko] Main line"]
    assert entry["source_hash"] == resource_hash(catalog.resources[0])


def test_english_keeps_only_headline_and_terms(fake_client, catalog, caches, jobs):
    translate(fake_client, catalog, caches, jobs, "direct")
    assert set(caches["en"]["resources"]["food-bank"]) == {
        "source_hash",
        "headline",
        "search_terms",
    }


def test_search_terms_are_cleaned(fake_client, catalog, caches, jobs):
    translate(fake_client, catalog, caches, jobs, "direct")
    assert caches["es"]["resources"]["tenant-help"]["search_terms"] == ["es word"]


def test_request_uses_structured_output_and_fallbacks(fake_client, catalog, caches, jobs):
    translate(fake_client, catalog, caches, jobs[:1], "direct")
    params = fake_client.messages.create.call_args.kwargs
    assert params["model"] == "claude-opus-5"
    assert params["output_config"]["format"]["type"] == "json_schema"
    assert params["extra_body"] == {"fallbacks": "default"}
    assert "(800) 555-0100" not in params["messages"][0]["content"]


@pytest.fixture
def respond_with(fake_client, message_factory):
    def install(mutate):
        original = fake_client.messages.create.side_effect

        def respond(**params):
            payload = json.loads(original(**params).content[0].text)
            mutate(payload)
            return message_factory(payload)

        fake_client.messages.create.side_effect = respond

    return install


@pytest.mark.parametrize(
    "mutate,reason",
    [
        pytest.param(
            lambda p: p["es"].update(description="Llame al (213) 555-0199"),
            "added phone numbers",
            id="invented-phone",
        ),
        pytest.param(
            lambda p: p["fa"].update(tip="www.scam.example"),
            "added phone numbers or web addresses",
            id="invented-url",
        ),
        pytest.param(
            lambda p: p["ko"].update(phone_labels=[]),
            "expected 1 phone labels",
            id="missing-phone-label",
        ),
    ],
)
def test_unsafe_translations_are_rejected(
    fake_client, respond_with, catalog, caches, jobs, mutate, reason
):
    respond_with(mutate)
    report = translate(fake_client, catalog, caches, jobs[:1], "direct")
    assert reason in report.failed["resource__food-bank"]
    assert caches["en"]["resources"] == {}


def test_refusal_is_recorded(fake_client, message_factory, catalog, caches, jobs):
    refusal = message_factory({}, stop_reason="refusal")
    fake_client.messages.create.side_effect = lambda **_: refusal
    report = translate(fake_client, catalog, caches, jobs, "direct")
    assert "refusal" in report.failed["resource__tenant-help"]


def test_api_errors_are_recorded(fake_client, catalog, caches, jobs):
    fake_client.messages.create.side_effect = RuntimeError("network down")
    report = translate(fake_client, catalog, caches, jobs, "direct")
    assert report.failed["resource__food-bank"] == "RuntimeError: network down"


def test_ui_translation_checks_placeholders(fake_client, respond_with, catalog, caches):
    respond_with(lambda payload: payload["strings"].update(results_for="Results"))
    report = translate(fake_client, catalog, caches, ui_jobs(catalog, caches, ("es",)), "direct")
    assert "results_for: placeholders changed" in report.failed["ui__es"]


def test_ui_translation_is_stored(fake_client, catalog, caches):
    translate(fake_client, catalog, caches, ui_jobs(catalog, caches, ("tr",)), "direct")
    assert caches["tr"]["ui"]["strings"]["search_button"] == "~Search"


@pytest.fixture
def batch_client(mocker, responder):
    client = mocker.Mock()
    submitted = []
    statuses = iter(["in_progress", "ended"])

    def create(requests):
        submitted.extend(requests)
        return SimpleNamespace(id="batch_1")

    def result(item):
        message = responder(item["params"])
        return SimpleNamespace(type="succeeded", message=message)

    client.messages.batches.create.side_effect = create
    client.messages.batches.retrieve.side_effect = lambda _: SimpleNamespace(
        processing_status=next(statuses)
    )
    client.messages.batches.results.side_effect = lambda _: [
        SimpleNamespace(custom_id=item["custom_id"], result=result(item)) for item in submitted
    ]
    return client


def test_batch_mode(mocker, batch_client, catalog, caches, jobs):
    mocker.patch("la_resiliency.runners.time.sleep")
    report = translate(batch_client, catalog, caches, jobs, "batch")
    assert sorted(report.translated) == ["resource__food-bank", "resource__tenant-help"]
    assert batch_client.messages.batches.retrieve.call_count == 2
    assert "extra_body" not in batch_client.messages.batches.create.call_args.kwargs


def test_batch_failures_are_recorded(batch_client, catalog, caches, jobs):
    batch_client.messages.batches.results.side_effect = lambda _: [
        SimpleNamespace(custom_id="resource__food-bank", result=SimpleNamespace(type="expired"))
    ]
    outcomes = dict(run_batch(batch_client, {"resource__food-bank": {}}, sleep=lambda _: None))
    assert str(outcomes["resource__food-bank"]) == "batch request expired"


@pytest.mark.parametrize(
    "mode,cost,text",
    [
        pytest.param("direct", 25.0, "about $25.00", id="direct"),
        pytest.param("batch", 12.5, "about $12.50", id="batch-half-price"),
        pytest.param("claude-code", 0.0, "covered by your Claude plan", id="subscription"),
    ],
)
def test_report_cost(mode, cost, text):
    report = Report(mode)
    report.usage["output_tokens"] = 1_000_000
    assert (report.cost, report.cost_text) == (cost, text)


def test_claude_code_translates(fake_claude_code, catalog, caches, jobs):
    report = translate(None, catalog, caches, jobs, "claude-code")
    assert sorted(report.translated) == ["resource__food-bank", "resource__tenant-help"]
    assert (
        caches["fa"]["resources"]["food-bank"]["description"] == "[fa] Free groceries every week."
    )
    assert report.usage["output_tokens"] == 600


def test_claude_code_command_is_isolated(monkeypatch, fake_claude_code, catalog, caches, jobs):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-be-used")
    translate(None, catalog, caches, jobs[:1], "claude-code")
    args, kwargs = fake_claude_code.call_args.args[0], fake_claude_code.call_args.kwargs
    assert args[:2] == ["claude", "-p"]
    assert {"--safe-mode", "--no-session-persistence", "--strict-mcp-config"} <= set(args)
    assert args[args.index("--tools") + 1] == ""
    assert args[args.index("--model") + 1] == "claude-opus-5"
    assert json.loads(args[args.index("--json-schema") + 1])["required"] == list(LLM_LANGS)
    assert "ANTHROPIC_API_KEY" not in kwargs["env"]
    assert json.loads(kwargs["input"])["resource"]["name"] == "Sample Food Bank"


@pytest.mark.parametrize(
    "stdout,returncode,reason",
    [
        pytest.param(
            '{"subtype": "success", "is_error": true, "result": "Claude usage limit reached"}',
            1,
            "usage limit reached",
            id="plan-limit",
        ),
        pytest.param("not json", 1, "claude exited 1: boom", id="crash"),
        pytest.param(
            '{"subtype": "error_max_turns", "is_error": false}',
            0,
            "claude exited 0",
            id="no-output",
        ),
    ],
)
def test_claude_code_failures_are_recorded(
    mocker, fake_claude_code, process_factory, catalog, caches, jobs, stdout, returncode, reason
):
    fake_claude_code.side_effect = lambda *a, **k: process_factory(stdout, returncode, "boom")
    report = translate(None, catalog, caches, jobs[:1], "claude-code")
    assert reason in report.failed["resource__food-bank"]


def test_missing_claude_code_is_a_setup_error(mocker, catalog, caches, jobs):
    mocker.patch("la_resiliency.runners.shutil.which", return_value=None)
    with pytest.raises(DataError):
        translate(None, catalog, caches, jobs, "claude-code")


def test_progress_callback_sees_each_result(fake_claude_code, catalog, caches, jobs):
    seen = []
    translate(None, catalog, caches, jobs, "claude-code", on_result=lambda cid, _: seen.append(cid))
    assert sorted(seen) == ["resource__food-bank", "resource__tenant-help"]


@pytest.mark.parametrize(
    "terms,expected",
    [
        pytest.param([" renta ", "renta", ""], ["renta"], id="dedupe-strip"),
        pytest.param(["call 888-624-4752", "ayuda"], ["ayuda"], id="drop-phone"),
        pytest.param(["https://x.org", "casa"], ["casa"], id="drop-url"),
    ],
)
def test_clean_terms(terms, expected):
    assert clean_terms(terms) == expected


@pytest.mark.parametrize(
    "source,translated,expected",
    [
        pytest.param({"a": "Call (888) 624-4752"}, "Llame al (888) 624-4752", set(), id="same"),
        pytest.param({"a": "110,000 people"}, "110.000 personas", set(), id="big-number"),
        pytest.param({"a": ""}, "۸۸۸-۶۲۴-۴۷۵۲", {"8886244752"}, id="persian-digits"),
    ],
)
def test_new_contacts(source, translated, expected):
    assert new_contacts(source, translated) == expected
