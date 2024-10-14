from typing import Literal

from parser import FillData

LINK_ICONS = {
    "YouTube": ("fa-brands", "fa-youtube"),
    "soundgasm": ("fa-solid", "fa-headphones"),
    "Patreon": ("fa-brands", "fa-patreon"),
    "Reddit": ("fa-brands", "fa-reddit-alien"),
    "Google Docs": ("fa-brands", "fa-google-drive"),
    "scriptbin": ("fa-solid", "fa-file-lines")
}


def icon(*fa_classes: str, direction: Literal["left", "right"]) -> str:
    """Create a font awesome icon."""
    class_str = " ".join(fa_classes)
    return f"""<i class="icon {class_str}"></i>"""


def attendant_va_icon() -> str:
    return icon("fa-solid", "fa-star", direction="right")


def self_fill_icon() -> str:
    return icon("fa-solid", "fa-crown", direction="right")


def make_header_icons(fill: FillData, attendant_va: list[str] | None) -> str:
    should_use_attendant = bool(attendant_va and set(attendant_va) & set(fill.creators))
    should_use_self_fill = "lilellia" in fill.creators

    attendant = attendant_va_icon() if should_use_attendant else ""
    self_fill = self_fill_icon() if should_use_self_fill else ""
    interior = f"{attendant}{self_fill}"

    return f"""<div class="icon">{interior}</div>""" if interior else ""


def get_link_icon_classes(label: str) -> tuple[str, ...]:
    if label.startswith("r/") or label.startswith("u/"):
        return LINK_ICONS["Reddit"]

    for key, value in LINK_ICONS.items():
        if label.startswith(key):
            return value

    raise ValueError(f"unknown label: {label}")


def make_link_icon(label: str) -> str:
    return icon(*get_link_icon_classes(label), direction="left")
