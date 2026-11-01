import httpx
import pytest

from la_resiliency.links import check_links, links_report

STATUSES = {
    "https://ok.example/": 200,
    "https://gone.example/": 404,
    "https://blocks-bots.example/": 403,
}


@pytest.fixture
def transport():
    def handler(request):
        url = str(request.url)
        if url == "https://down.example/":
            raise httpx.ConnectError("no route", request=request)
        return httpx.Response(STATUSES[url])

    return httpx.MockTransport(handler)


@pytest.fixture
def resources(catalog):
    base = catalog.resources[0]
    urls = [*STATUSES, "https://down.example/", "https://ok.example/"]
    return [base.model_copy(update={"id": f"r{i}", "url": url}) for i, url in enumerate(urls)]


def test_check_links_groups_shared_urls(resources, transport):
    results = check_links(resources, workers=2, transport=transport)
    verdicts = {result.url: (result.verdict, result.ids) for result in results}
    assert verdicts["https://ok.example/"] == ("ok", ("r0", "r4"))
    assert verdicts["https://gone.example/"][0] == "broken"
    assert verdicts["https://blocks-bots.example/"][0] == "blocked"
    assert verdicts["https://down.example/"][0] == "broken"


def test_links_report(resources, transport):
    text = links_report(check_links(resources, transport=transport))
    assert "Broken links" in text and "`r1`" in text and "ConnectError" in text
    assert "block automated checks" in text


def test_links_report_all_ok():
    assert links_report([]) == "All 0 links responded."
