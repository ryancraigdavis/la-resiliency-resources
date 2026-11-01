import pytest

from la_resiliency.report import Changes, diff_resources, sync_report
from la_resiliency.translate import Report


def test_diff_resources(catalog):
    before = catalog.resources
    after = [before[0].model_copy(update={"tip": "New tip"}), before[1]]
    after.append(before[2].model_copy(update={"id": "brand-new"}))
    assert diff_resources(before, after) == Changes(
        added=["brand-new"], removed=["retired-program"], changed=["food-bank"]
    )


@pytest.mark.parametrize(
    "failed,expected",
    [
        pytest.param({}, "Translated 1 item(s) (batch mode), about $0.00.", id="clean"),
        pytest.param({}, "(claude-code mode), covered by your Claude plan.", id="subscription"),
        pytest.param({"ui__fa": "boom"}, "- `ui__fa`: boom", id="failures-listed"),
    ],
)
def test_sync_report(failed, expected):
    mode = "claude-code" if "claude-code" in expected else "batch"
    report = Report(mode, translated=["resource__x"], failed=failed)
    text = sync_report(Changes([], [], ["x"]), report, "All 3 links responded.")
    assert expected in text
    assert "- Changed: `x`" in text
