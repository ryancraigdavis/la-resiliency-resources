from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str
    native: str
    dir: str
    prompt: str


LANGUAGES = (
    Language("en", "English", "ltr", "English"),
    Language("es", "Español", "ltr", "Spanish, as spoken by Latin American families in LA"),
    Language("ko", "한국어", "ltr", "Korean, polite formal style (합니다/하세요)"),
    Language("zh-hans", "简体中文", "ltr", "Simplified Chinese (Mandarin)"),
    Language("zh-hant", "繁體中文", "ltr", "Traditional Chinese"),
    Language("fa", "فارسی", "rtl", "Persian (Farsi), as used by Iranian Americans"),
    Language("tr", "Türkçe", "ltr", "Turkish"),
)

BY_CODE = {language.code: language for language in LANGUAGES}
SITE_LANGS = tuple(language.code for language in LANGUAGES)
DERIVED = {"zh-hant": "zh-hans"}
LLM_LANGS = tuple(code for code in SITE_LANGS if code not in DERIVED)
TRANSLATED_LANGS = tuple(code for code in LLM_LANGS if code != "en")
SHEET_LANGS = ("en", "es", "ko", "zh", "fa", "tr")


def base_code(code: str) -> str:
    return code.split("-")[0]
