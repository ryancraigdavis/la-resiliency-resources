from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def resources(self) -> Path:
        return self.data / "resources.yaml"

    @property
    def categories(self) -> Path:
        return self.data / "categories.yaml"

    @property
    def ui(self) -> Path:
        return self.data / "ui.yaml"

    @property
    def i18n(self) -> Path:
        return self.data / "i18n"

    @property
    def overrides(self) -> Path:
        return self.i18n / "overrides"

    @property
    def site_data(self) -> Path:
        return self.root / "frontend" / "src" / "lib" / "data"

    def cache_file(self, lang: str) -> Path:
        return self.i18n / f"{lang}.json"

    def override_file(self, lang: str) -> Path:
        return self.overrides / f"{lang}.yaml"


def default_paths() -> Paths:
    return Paths(REPO_ROOT)
