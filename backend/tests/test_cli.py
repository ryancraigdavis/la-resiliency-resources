import pytest

from la_resiliency import cli
from la_resiliency.store import DataError


@pytest.fixture
def run(mocker, paths):
    mocker.patch("la_resiliency.cli.default_paths", return_value=paths)
    return cli.main


def test_validate(run, capsys):
    run(["validate"])
    assert "OK: 3 resources, 9 topics." in capsys.readouterr().out


def test_seed_csv(run, paths):
    out = paths.root / "seed.csv"
    run(["seed-csv", "--out", str(out)])
    assert out.read_text("utf-8").startswith("id,active,category")


def test_translate_dry_run_makes_no_calls_or_files(run, mocker, paths, capsys):
    client = mocker.patch("la_resiliency.cli.anthropic.Anthropic")
    run(["translate", "--dry-run"])
    assert "7 translation job(s). With --mode claude-code" in capsys.readouterr().out
    assert not client.called
    assert not paths.i18n.exists()


def test_translate_only_skips_ui(run, mocker, fake_client, paths, capsys):
    mocker.patch("la_resiliency.cli.anthropic.Anthropic", return_value=fake_client)
    run(["translate", "--mode", "direct", "--only", "tenant-help", "--langs", "es,en"])
    assert "Translated 1, failed 0 (about $0.02)." in capsys.readouterr().out
    assert paths.cache_file("es").exists()


def test_sync_without_sheet_url_fails(run, monkeypatch, capsys):
    monkeypatch.delenv("SHEET_CSV_URL", raising=False)
    with pytest.raises(SystemExit):
        run(["sync", "--dry-run"])
    assert "No Sheet URL" in capsys.readouterr().err


def test_sync_pulls_translates_and_reports(run, mocker, fake_client, paths, catalog):
    from la_resiliency.sheet import to_csv

    edited = [catalog.resources[0].model_copy(update={"tip": "Bring ID."}), catalog.resources[1]]
    mocker.patch("la_resiliency.cli.fetch_csv", return_value=to_csv(edited))
    mocker.patch("la_resiliency.cli.anthropic.Anthropic", return_value=fake_client)
    report = paths.root / "report.md"
    run(
        [
            "sync",
            "--mode",
            "direct",
            "--csv-url",
            "https://sheet",
            "--no-links",
            "--report",
            str(report),
        ]
    )
    text = report.read_text("utf-8")
    assert "- Changed: `food-bank`" in text and "- Removed: `retired-program`" in text
    assert (paths.site_data / "zh-hant.json").exists()
    assert "Bring ID." in paths.resources.read_text("utf-8")


def test_data_errors_exit_nonzero(run, mocker, capsys):
    mocker.patch("la_resiliency.cli.load_catalog", side_effect=DataError(["x: broken"]))
    with pytest.raises(SystemExit):
        run(["validate"])
    assert "- x: broken" in capsys.readouterr().err


def test_translate_with_claude_code_saves_progress(run, fake_claude_code, paths, capsys):
    run(["translate", "--only", "food-bank,tenant-help", "--langs", "ko"])
    out = capsys.readouterr().out
    assert "[2/2]" in out and "covered by your Claude plan" in out
    assert "food-bank" in paths.cache_file("ko").read_text("utf-8")
