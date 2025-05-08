from __future__ import annotations
import re
from datetime import timedelta

import jinja2

# a set containing tags that designate the script as NSFW
NSFW_TAGS = {"18+", "nsfw", "r18"}


def script_tag_classes(tag: str) -> str:
    """Determine the html classes that should be attached to this script tag.

    {{"wholesome" | script_tag_classes}}         => "script-tag"
    {{"18+" | script_tag_classes}}               => "script-tag nsfw-tag"
    """
    classes = ["script-tag"]

    if tag in NSFW_TAGS:
        classes.append("nsfw-tag")

    return " ".join(classes)


def script_classes(tags: list[str]) -> str:
    """Determine the html classes that should be attached to a script with these tags.
    """
    classes = ["container", "script-data"]

    if any_nsfw(tags):
        classes.append("blurred")

    return " ".join(classes)


def join_content_tags(tags: list[str]) -> str:
    """Return a string with all of the tags concatenated as [tag1][tag2][tag3]..."""
    return "".join(f"[{tag}]" for tag in tags)


def overlap_lists[T](haystack1: list[T], haystack2: list[T]) -> bool:
    """Return True when there is any overlap between the two lists.

    {{ ["a", "b"] | overlap_lists(["a"]) }}         => true
    {{ ["a", "b"] | overlap_lists(["c", "q"]) }}    => false
    """
    overlap = set(haystack1) & set(haystack2)
    return bool(overlap)


def any_nsfw(tags: list[str]) -> bool:
    """Determine whether a tag with these tags should be marked nsfw."""
    overlap = NSFW_TAGS & set(tags)
    return bool(overlap)


def summarise_gender(audience: str) -> str:
    """Summarise the gender for a fill, based on the speaker."""
    if re.match(r"^M+4", audience):
        gender = "male"
    elif re.match(r"^F+4", audience):
        gender = "female"
    else:
        gender = "neutral"

    return gender


def serialise(text: str) -> str:
    patterns = {
        "~": "-",
        " ": "-",
        "'": "",
        "\"": "",
        "&": "and"
    }

    for string, replace in patterns.items():
        text = text.lower().replace(string, replace)

    return text


def make_csv(items: list[str]) -> str:
    return ", ".join(items)


def format_timedelta(t: timedelta | None) -> str:
    if not t:
        return ""

    minutes, seconds = divmod(t.total_seconds(), 60)
    return f"{minutes:02.0f}:{seconds:02.0f}"


def render_series(s: dict[str, str | int] | None) -> str:
    if s is None:
        return ""

    return str(s.get("title", ""))


def render_series_index(s: dict[str, str | int] | None) -> str:
    if s is None:
        return ""

    return str(s.get("index", ""))



NEW_FILTERS = {
    "c_script_tag_classes": script_tag_classes,
    "c_join_content_tags": join_content_tags,
    "c_overlap_lists": overlap_lists,
    "c_any_nsfw": any_nsfw,
    "c_summarise_gender": summarise_gender,
    "c_serialise": serialise,
    "c_script_classes": script_classes,
    "c_make_csv": make_csv,
    "c_format_timedelta": format_timedelta,
    "c_render_series": render_series,
    "c_render_series_index": render_series_index
}


def add_all_filters(env: jinja2.Environment) -> None:
    """Add all of the filters to the given environment."""
    env.filters.update(NEW_FILTERS)
