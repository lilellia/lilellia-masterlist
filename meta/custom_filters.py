import re

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


def overlap_lists[T](haystack1: list[T], haystack2: list[T]) -> bool:
    """Return True when there is any overlap between the two lists.

    {{ ["a", "b"] | overlap_lists(["a"]) }}         => true
    {{ ["a", "b"] | overlap_lists(["c", "q"]) }}    => false
    """
    overlap = set(haystack1) & set(haystack2)
    return bool(overlap)


def any_nsfw(tags: list[str]) -> bool:
    """Determine whether a tag with these tags should be marked nsfw."""
    return any(tag in NSFW_TAGS for tag in tags)


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


NEW_FILTERS = {
    "c_script_tag_classes": script_tag_classes,
    "c_overlap_lists": overlap_lists,
    "c_any_nsfw": any_nsfw,
    "c_summarise_gender": summarise_gender,
    "c_serialise": serialise,
    "c_script_classes": script_classes
}


def add_all_filters(env: jinja2.Environment) -> None:
    """Add all of the filters to the given environment."""
    env.filters.update(NEW_FILTERS)