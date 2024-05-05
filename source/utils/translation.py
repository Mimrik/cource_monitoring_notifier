"""Translation module."""
import gettext
import os
from enum import StrEnum


source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
translation_path = os.path.abspath(os.path.join(source_path, os.pardir, "translations"))


class LanguageTitle(StrEnum):
    """LanguageTitle."""

    RU = "🇷🇺 русский"
    EN = "🇬🇧 english"


class LanguageCode(StrEnum):
    """LanguageCode."""

    RU = "ru_RU.UTF-8"
    EN = "en_US.UTF-8"


LANGUAGE_CODE_TO_TITLE = {
    LanguageCode.RU: LanguageTitle.RU,
    LanguageCode.EN: LanguageTitle.EN
}


LANGUAGE_CODE_TO_TRANSLATION = {
    LanguageCode.RU: gettext.translation(
        "course_monitoring_notifier", translation_path, ["ru_RU.UTF-8"], fallback=True
    ),
    LanguageCode.EN: gettext.NullTranslations(),
}


def _(text: str, language_code: LanguageCode) -> str:
    """Translate."""
    return LANGUAGE_CODE_TO_TRANSLATION[language_code].gettext(text)
