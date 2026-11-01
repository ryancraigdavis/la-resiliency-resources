from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import httpx

from la_resiliency.models import Resource

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
BLOCKED_STATUSES = {401, 403, 405, 429, 999}


@dataclass(frozen=True)
class LinkResult:
    url: str
    ids: tuple[str, ...]
    status: int | None
    error: str = ""

    @property
    def verdict(self) -> str:
        ok = self.status is not None and 200 <= self.status < 400
        blocked = self.status in BLOCKED_STATUSES
        return "ok" if ok else "blocked" if blocked else "broken"


def urls_by_resource(resources: list[Resource]) -> dict[str, tuple[str, ...]]:
    grouped = defaultdict(list)
    for resource in resources:
        grouped[resource.url].append(resource.id)
    return {url: tuple(ids) for url, ids in grouped.items() if url}


def fetch_status(client: httpx.Client, url: str) -> tuple[int | None, str]:
    try:
        outcome = (client.get(url).status_code, "")
    except httpx.HTTPError as exc:
        outcome = (None, f"{type(exc).__name__}: {exc}")
    return outcome


def check_links(resources: list[Resource], workers: int = 8, transport=None) -> list[LinkResult]:
    targets = urls_by_resource(resources)
    options = {"headers": BROWSER_HEADERS, "follow_redirects": True, "timeout": 20}
    options |= {"transport": transport} if transport else {}
    with httpx.Client(**options) as client, ThreadPoolExecutor(workers) as pool:
        statuses = list(pool.map(lambda url: fetch_status(client, url), targets))
    return [
        LinkResult(url, ids, status, error)
        for (url, ids), (status, error) in zip(targets.items(), statuses, strict=True)
    ]


def link_line(result: LinkResult) -> str:
    detail = result.error or f"HTTP {result.status}"
    return f"- `{', '.join(result.ids)}`: {result.url} ({detail})"


def links_report(results: list[LinkResult]) -> str:
    groups = defaultdict(list)
    for result in results:
        groups[result.verdict].append(link_line(result))
    sections = [
        ("Broken links (please fix in the Sheet)", groups["broken"]),
        ("Sites that block automated checks (open by hand once)", groups["blocked"]),
    ]
    body = [f"### {title}\n" + "\n".join(lines) for title, lines in sections if lines]
    return "\n\n".join(body) or f"All {len(results)} links responded."
