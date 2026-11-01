import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

from la_resiliency.cache import Caches, Job, load_caches, prune, resource_jobs, save_caches, ui_jobs
from la_resiliency.export import active, export_site
from la_resiliency.languages import LLM_LANGS
from la_resiliency.links import check_links, links_report
from la_resiliency.paths import Paths, default_paths
from la_resiliency.report import Changes, changes_section, diff_resources, sync_report
from la_resiliency.sheet import fetch_csv, parse_csv, to_csv
from la_resiliency.store import (
    Catalog,
    DataError,
    check_catalog,
    dump_resources,
    load_catalog,
    parse_resources,
    write_text,
)
from la_resiliency.translate import MODES, PRICES_PER_MTOK, Report, request_params, translate

ESTIMATED_OUTPUT_PER_LANG = {"resource": 350, "ui": 1200}


def split_arg(value: str | None) -> tuple[str, ...]:
    return tuple(part.strip() for part in (value or "").split(",") if part.strip())


def sheet_url(args) -> str:
    url = args.csv_url or os.environ.get("SHEET_CSV_URL", "")
    if not url:
        raise DataError(["No Sheet URL: set SHEET_CSV_URL or pass --csv-url"])
    return url


def pull(paths: Paths, url: str, write: bool) -> tuple[Changes, Catalog]:
    current = load_catalog(paths)
    resources = parse_resources(parse_csv(fetch_csv(url)))
    pulled = check_catalog(Catalog(resources, current.categories, current.ui))
    if write:
        dump_resources(resources, paths.resources)
    return diff_resources(current.resources, resources), pulled


def plan_jobs(catalog: Catalog, caches: Caches, args) -> list[Job]:
    langs = split_arg(args.langs) or LLM_LANGS
    only = set(split_arg(args.only))
    resources = [
        job for job in resource_jobs(catalog, caches, langs) if not only or job.key in only
    ]
    return ([] if only else ui_jobs(catalog, caches, langs)) + resources


def estimate_cost(jobs: list[Job], catalog: Catalog) -> float:
    prompt_chars = sum(len(json.dumps(request_params(job, catalog))) for job in jobs)
    output = sum(len(job.langs) * ESTIMATED_OUTPUT_PER_LANG[job.kind] for job in jobs)
    spend = (prompt_chars / 3) * PRICES_PER_MTOK["input_tokens"]
    return (spend + output * PRICES_PER_MTOK["output_tokens"]) / 1_000_000


def plan_text(jobs: list[Job], catalog: Catalog) -> str:
    lines = [f"  {job.kind} {job.key}: {', '.join(job.langs)}" for job in jobs]
    cost = estimate_cost(jobs, catalog)
    header = (
        f"{len(jobs)} translation job(s). With --mode claude-code this uses your Claude plan; "
        f"through the API it would cost roughly ${cost:.2f} (direct) or ${cost / 2:.2f} (batch)."
    )
    return "\n".join([header, *lines])


def api_client():
    return anthropic.Anthropic()


def no_client():
    return None


CLIENTS = {"claude-code": no_client, "direct": api_client, "batch": api_client}


def progress_printer(paths: Paths, caches: Caches, total: int):
    def on_result(custom_id: str, report: Report) -> None:
        save_caches(paths, caches)
        done = len(report.translated) + len(report.failed)
        status = "ok" if custom_id in report.translated else f"FAILED {report.failed[custom_id]}"
        print(f"[{done}/{total}] {custom_id}: {status}", flush=True)

    return on_result


def execute(paths: Paths, catalog: Catalog, caches: Caches, jobs: list[Job], mode: str) -> Report:
    on_result = progress_printer(paths, caches, len(jobs))
    report = translate(CLIENTS[mode](), catalog, caches, jobs, mode, on_result=on_result)
    save_caches(paths, caches)
    return report


def skip(paths: Paths, catalog: Catalog, caches: Caches, jobs: list[Job], mode: str) -> Report:
    return Report(mode)


def run_translation(paths: Paths, catalog: Catalog, args) -> Report:
    caches = prune(load_caches(paths), {resource.id for resource in catalog.resources})
    jobs = plan_jobs(catalog, caches, args)
    print(plan_text(jobs, catalog))
    action = skip if args.dry_run or not jobs else execute
    return action(paths, catalog, caches, jobs, args.mode)


def cmd_validate(args, paths: Paths) -> None:
    catalog = load_catalog(paths)
    print(f"OK: {len(catalog.resources)} resources, {len(catalog.categories)} topics.")


def cmd_seed_csv(args, paths: Paths) -> None:
    write_text(Path(args.out), to_csv(load_catalog(paths).resources))
    print(f"Wrote {args.out}. Import it into the Resources tab of the Google Sheet.")


def cmd_pull(args, paths: Paths) -> None:
    changes, _ = pull(paths, sheet_url(args), write=True)
    print(changes_section(changes))


def cmd_translate(args, paths: Paths) -> None:
    report = run_translation(paths, load_catalog(paths), args)
    summary = f"Translated {len(report.translated)}, failed {len(report.failed)}"
    print(f"{summary} ({report.cost_text}).")
    for custom_id, reason in report.failed.items():
        print(f"  FAILED {custom_id}: {reason}")


def cmd_export(args, paths: Paths) -> None:
    langs = export_site(paths, load_catalog(paths), load_caches(paths))
    print(f"Exported site data for: {', '.join(langs)}")


def cmd_links(args, paths: Paths) -> None:
    print(links_report(check_links(active(load_catalog(paths)))))


def cmd_sync(args, paths: Paths) -> None:
    pulled = pull(paths, sheet_url(args), write=not args.dry_run) if args.pull else None
    changes, catalog = pulled or (Changes([], [], []), load_catalog(paths))
    report = run_translation(paths, catalog, args)
    if not args.dry_run:
        export_site(paths, catalog, load_caches(paths))
    links = links_report(check_links(active(catalog))) if args.links else "Skipped."
    text = sync_report(changes, report, links)
    if args.report:
        write_text(Path(args.report), text)
    print(text)


def add_translate_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true", help="plan only; no API calls or writes")
    parser.add_argument(
        "--mode",
        choices=MODES,
        default="claude-code",
        help="claude-code uses your Claude subscription; direct/batch use ANTHROPIC_API_KEY",
    )
    parser.add_argument("--only", help="comma-separated resource ids (skips UI text)")
    parser.add_argument("--langs", help="comma-separated language codes")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="la-resiliency")
    commands = parser.add_subparsers(required=True)
    commands.add_parser("validate", help="check data files").set_defaults(func=cmd_validate)
    seed = commands.add_parser("seed-csv", help="write resources as CSV for the Sheet")
    seed.add_argument("--out", default="resources.csv")
    seed.set_defaults(func=cmd_seed_csv)
    pull_cmd = commands.add_parser("pull", help="update data/resources.yaml from the Sheet")
    pull_cmd.add_argument("--csv-url")
    pull_cmd.set_defaults(func=cmd_pull)
    translate_cmd = commands.add_parser("translate", help="translate new or changed text")
    add_translate_options(translate_cmd)
    translate_cmd.set_defaults(func=cmd_translate)
    commands.add_parser("export", help="write site JSON").set_defaults(func=cmd_export)
    commands.add_parser("check-links", help="check resource websites").set_defaults(func=cmd_links)
    sync = commands.add_parser("sync", help="pull, translate, export, and check links")
    add_translate_options(sync)
    sync.add_argument("--csv-url")
    sync.add_argument("--no-pull", dest="pull", action="store_false")
    sync.add_argument("--no-links", dest="links", action="store_false")
    sync.add_argument("--report", help="write a Markdown summary to this path")
    sync.set_defaults(func=cmd_sync)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args, default_paths())
    except DataError as exc:
        print("Data problems:\n" + "\n".join(f"- {p}" for p in exc.problems), file=sys.stderr)
        raise SystemExit(1) from exc
