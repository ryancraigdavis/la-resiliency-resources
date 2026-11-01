from dataclasses import dataclass

from la_resiliency.models import Resource
from la_resiliency.translate import Report


@dataclass(frozen=True)
class Changes:
    added: list[str]
    removed: list[str]
    changed: list[str]

    @property
    def any(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def diff_resources(before: list[Resource], after: list[Resource]) -> Changes:
    old = {resource.id: resource for resource in before}
    new = {resource.id: resource for resource in after}
    return Changes(
        added=[rid for rid in new if rid not in old],
        removed=[rid for rid in old if rid not in new],
        changed=[rid for rid in new if rid in old and old[rid] != new[rid]],
    )


def id_list(title: str, ids: list[str]) -> str:
    return f"- {title}: " + (", ".join(f"`{rid}`" for rid in ids) or "none")


def changes_section(changes: Changes) -> str:
    lines = [
        id_list("Added", changes.added),
        id_list("Changed", changes.changed),
        id_list("Removed", changes.removed),
    ]
    return "## Resource changes\n" + "\n".join(lines)


def translation_section(report: Report) -> str:
    failures = [f"- `{cid}`: {reason}" for cid, reason in report.failed.items()]
    summary = (
        f"Translated {len(report.translated)} item(s) ({report.mode} mode), {report.cost_text}."
    )
    retry = "\n\nFailed (English is shown until the next run succeeds):\n" + "\n".join(failures)
    return "## Translations\n" + summary + (retry if failures else "")


def sync_report(changes: Changes, translation: Report, links: str) -> str:
    sections = [
        "# Resource sync",
        changes_section(changes),
        translation_section(translation),
        "## Link check\n" + links,
    ]
    return "\n\n".join(sections) + "\n"
