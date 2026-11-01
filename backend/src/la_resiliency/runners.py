import contextlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from la_resiliency.store import DataError

FALLBACK_BETA = "server-side-fallback-2026-07-01"
USAGE_KEYS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)
CLAUDE_CODE_TIMEOUT_SECONDS = 900
WORKERS = 4


class TranslationError(Exception):
    pass


@dataclass(frozen=True)
class Outcome:
    payload: dict
    usage: dict[str, int]


Results = Iterator[tuple[str, "Outcome | BaseException"]]


def capture(call: Callable[[], Outcome]) -> "Outcome | BaseException":
    try:
        result = call()
    except Exception as exc:  # recorded per job and retried on the next run
        result = exc
    return result


def run_parallel(requests: dict[str, dict], call: Callable[[dict], Outcome]) -> Results:
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(capture, lambda p=params: call(p)): cid for cid, params in requests.items()
        }
        for future in as_completed(futures):
            yield futures[future], future.result()


def usage_of(source) -> dict[str, int]:
    values = source if isinstance(source, dict) else vars(source)
    return {key: values.get(key) or 0 for key in USAGE_KEYS}


# Anthropic API (pay per token) -----------------------------------------------------------------


def message_outcome(message) -> Outcome:
    if message.stop_reason != "end_turn":
        raise TranslationError(f"model stopped with '{message.stop_reason}'")
    text = next(block.text for block in message.content if block.type == "text")
    return Outcome(json.loads(text), usage_of(message.usage))


def call_direct(client, params: dict) -> Outcome:
    message = client.messages.create(
        **params,
        extra_headers={"anthropic-beta": FALLBACK_BETA},
        extra_body={"fallbacks": "default"},
    )
    return message_outcome(message)


def run_direct(client, requests: dict[str, dict]) -> Results:
    return run_parallel(requests, lambda params: call_direct(client, params))


def wait_for_batch(client, batch_id: str, poll_seconds: float, sleep: Callable) -> None:
    while client.messages.batches.retrieve(batch_id).processing_status != "ended":
        sleep(poll_seconds)


def batch_outcome(item) -> "Outcome | BaseException":
    result = item.result
    failure = TranslationError(f"batch request {result.type}")
    return (
        capture(lambda: message_outcome(result.message)) if result.type == "succeeded" else failure
    )


def run_batch(client, requests: dict[str, dict], poll_seconds: float = 30, sleep=None) -> Results:
    items = [{"custom_id": cid, "params": params} for cid, params in requests.items()]
    batch = client.messages.batches.create(requests=items)
    print(f"Submitted batch {batch.id} with {len(items)} requests; waiting for results...")
    wait_for_batch(client, batch.id, poll_seconds, sleep or time.sleep)
    for item in client.messages.batches.results(batch.id):
        yield item.custom_id, batch_outcome(item)


# Claude Code (uses the logged-in Claude subscription) ------------------------------------------


def claude_code_args(params: dict) -> list[str]:
    output = params["output_config"]
    return [
        "claude",
        "-p",
        "--model",
        params["model"],
        "--effort",
        output["effort"],
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(output["format"]["schema"]),
        "--system-prompt",
        params["system"][0]["text"],
        "--tools",
        "",
        "--no-session-persistence",
        "--safe-mode",
        "--strict-mcp-config",
    ]


def subscription_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key != "ANTHROPIC_API_KEY"}


def parse_cli_json(stdout: str) -> dict:
    data = {}
    with contextlib.suppress(json.JSONDecodeError):
        data = json.loads(stdout)
    return data if isinstance(data, dict) else {}


def cli_outcome(completed: subprocess.CompletedProcess) -> Outcome:
    data = parse_cli_json(completed.stdout)
    succeeded = data.get("subtype") == "success" and not data.get("is_error")
    if not (succeeded and isinstance(data.get("structured_output"), dict)):
        detail = data.get("result") or completed.stderr.strip()[-400:] or completed.stdout[-400:]
        raise TranslationError(f"claude exited {completed.returncode}: {detail}")
    return Outcome(data["structured_output"], usage_of(data.get("usage", {})))


def call_claude_code(params: dict) -> Outcome:
    with tempfile.TemporaryDirectory(prefix="la-resiliency-") as workdir:
        completed = subprocess.run(
            claude_code_args(params),
            input=params["messages"][0]["content"],
            capture_output=True,
            text=True,
            timeout=CLAUDE_CODE_TIMEOUT_SECONDS,
            cwd=workdir,
            env=subscription_env(),
            check=False,
        )
    return cli_outcome(completed)


def require_claude_code() -> None:
    if not shutil.which("claude"):
        raise DataError(["Claude Code (`claude`) is not installed or not on PATH"])


def run_claude_code(client, requests: dict[str, dict]) -> Results:
    require_claude_code()
    yield from run_parallel(requests, call_claude_code)


RUNNERS = {"claude-code": run_claude_code, "direct": run_direct, "batch": run_batch}
