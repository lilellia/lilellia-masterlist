import re
from datetime import datetime
from io import StringIO
from itertools import count
from operator import attrgetter
from pathlib import Path
from typing import Any, Iterator, Iterable, Literal, Collection

from parser import FillData, Script, SeriesData, WordCountData, parse
from build_icons import make_header_icons, make_link_icon

# a set containing tags that designate the script as NSFW
NSFW_TAGS = {"18+", "nsfw", "r18"}


def reverse_enumerate[T](seq: Collection[T], *, start: int = 1) -> Iterator[tuple[int, T]]:
    """Return an enumeration of (index, item), but numbered n, n-1, ..., 1"""
    n = len(seq)
    for i, item in zip(range(n + (start - 1), start - 1, -1), seq):
        yield i, item


def tagged(value: Any, tag: str) -> str:
    """Enclose the value in the given tag."""
    return f"<{tag}>{value}</{tag}>"


def html_header() -> str:
    return f"""\
<html>
<head>
    <meta charset="utf-8">
    <title>lilellia's masterlist</title>
    <link href="static/css/main.css" rel="stylesheet">
    <link href="static/css/series.css" rel="stylesheet">
    <link rel="icon" type="image/x-icon" href="static/favicon.png">
    <script src="https://kit.fontawesome.com/d17f614691.js" crossorigin="anonymous"></script>
    <script type="text/javascript" src="static/js/filter.js"></script>
    <script>
        window.onload = function() {{
            for(const element of document.getElementsByClassName("blurred")) {{
                element.onclick = function() {{
                    element.classList.remove("blurred");
                }}
            }}
        }};
    </script>
</head>"""


def introduction() -> str:
    fp = Path(__file__).parent / "introduction.html"
    return fp.read_text(encoding="utf-8")


def introduction_fills_page() -> str:
    fp = Path(__file__).parent / "introduction-fills-page.html"
    return fp.read_text(encoding="utf-8")


def html_filter_section(
        num_scripts: int,
        num_fills: int,
        series_names: Iterable[str],
        audience_tags: Iterable[str],
        filled_by: Iterable[str],
) -> str:

    kwargs = {
        "num_scripts": num_scripts,
        "num_fills": num_fills,
        "series": "\n".join(f"""<option class="{serialise(s)}" value="{s}">{s}</option>""" for s in sorted(series_names)),
        "audience": "\n".join(f"""<option value="{tag}">{tag}</option>""" for tag in sorted(audience_tags)),
        "filled_by": "\n".join(f"""<option value="{name}">{name}</option>""" for name in sorted(filled_by, key=str.lower)),
    }

    fp = Path(__file__).parent / "filter-section.html"
    template = fp.read_text(encoding="utf-8")

    return template.format(**kwargs)


def html_closer() -> str:
    return """\
</body>
</html>
"""


def extract_priority_fill_link(fill: FillData) -> str:
    if link := fill.links.get("YouTube"):
        return link

    if link := fill.links.get("soundgasm"):
        return link

    if link := fill.links.get("Patreon"):
        return link

    raise ValueError(f"could not find link for fill: {fill.title}")


def summarise_gender(audience: str) -> str:
    if re.match(r"^M+4", audience):
        gender = "male"
    elif re.match(r"^F+4", audience):
        gender = "female"
    else:
        gender = "neutral"

    return gender


def make_label_text(label: str) -> str:
    if not label:
        return ""
    
    pars = [f"""<div>({par})</div>""" for par in label.splitlines()]
    result = "\n".join(pars)
    return f"""<div class="fill-label">{result}</div>"""


def htmlify_fill(fill: FillData, *, attendant_va: list[str] | None) -> str:
    priority_link = extract_priority_fill_link(fill)
    label = make_label_text(fill.label)
    tag_class = f"fill-{summarise_gender(fill.audience)}"

    header_icons = make_header_icons(fill, attendant_va)

    creator_line = f"""<span class="fill-creator">{", ".join(fill.creators)}</span>"""

#     if header_icons:
#         creator_line = f"""\
# <div class="tooltip">
#     {creator_line}
#     <div class="tooltiptext">
#         {header_icons}
#     </div>
# </div>
# """

    return f"""\
    <div class="fill-details {tag_class}">
            {creator_line}
            {label}
            <div class="fill-date">{fill.date.strftime("%d %b %Y")}</div>
            <span>{make_links(fill.links)}</span>
            {header_icons}
    </div>
"""


def htmlify_fills_summary(fills: list[FillData], *, attendant_va: list[str] | None) -> str:
    if not fills:
        return ""

    fill_tags = "\n".join(htmlify_fill(f, attendant_va=attendant_va) for f in fills)
    return f"""\
        <div class="fill-summary">
            <p><b>Fills (<span class="fill-count">{len(fills)}</span>):</b></p>
            <div class="script-fills">
{fill_tags}
            </div>
        </div>
"""


def htmlify_series_data(series: SeriesData | None) -> str:
    if series is None:
        return ""

    class_ = serialise(series.title)

    return f"""\
        <ul class="script-tags">
            <li class="script-tag series-tag {class_}">Series: <span class="series-title">{series.title}</span> (Part <span class="series-index">{series.index}</span>)</li>
        </ul>
"""


def script_tag_classes(tag: str) -> str:
    classes = ["script-tag"]

    if tag in NSFW_TAGS:
        classes.append("nsfw-tag")

    return " ".join(classes)


def is_nsfw(script: Script) -> bool:
    """Determine whether this script is marked as NSFW"""
    return any(tag in NSFW_TAGS for tag in script.tags)


def serialise(text: str) -> str:
    return text.lower().replace("∼", "-").replace(" ", "-").replace("'", "").replace('"', "").replace("&", "and")


def htmlify_wordcount(words: WordCountData) -> str:
    num_speakers = len(words.spoken.keys())
    full = words.all_spoken

    if num_speakers == 1:
        content = format(full, ",")
    elif num_speakers >= 2:
        individual = "+".join(format(v, ",") for v in words.spoken.values())
        content = f"{individual} (={full:,})"
    else:
        raise ValueError(f"invalid speaker count: {words}")

    return f"""\t\t\t<li class="script-tag meta-tag">{content} words</li>"""



def _make_link(label: str, href: str) -> str:
    link_icon = make_link_icon(label)

    return f"""\
    <div>
        <div class="tooltip">
            <a href="{href}">{link_icon}</a>
            <div class="tooltiptext">
                {label}
            </div>
        </div>
    </div>
"""

def make_script_links(links: dict[str, str]) -> str:
    """Convert a dict of {label: href} to a tooltip list of <a> tags"""

    li_string = " ".join(_make_link(label, href) for label, href in links.items())
    return f"""\
        <div class="script-links">
            {li_string}
        </div>
    """


def make_links(links: dict[str, str]) -> str:
    """Convert a dict of {label: href} to a tooltip list of <a> tags"""

    li_string = " ".join(_make_link(label, href) for label, href in links.items())
    return f"""\
        <div class="fill-links">
            {li_string}
        </div>
"""


def htmlify(script: Script, *, index: int) -> str:
    # handle all the "content" tags
    assert script.published is not None
    audience_tag = "\n".join(
        f"""<li class="script-tag audience-tag {atag.lower()}">{atag.upper()}</li>"""
        for atag in script.audience
    )

    script_links = make_script_links(script.links.combine_dict())

    tags = "\n".join(f"""<li class="{script_tag_classes(tag)}">{tag}</li>""" for tag in script.tags)

    summary = "\n".join(f"<p>{par}</p>" for par in script.summary.splitlines())

    classes = ["container", "script-data"]
    if is_nsfw(script):
        classes.append("blurred")

    return f"""\
    <div class="{' '.join(classes)}" id={serialise(script.title)}>
        <span class="script-index">{script.published.strftime("%d %b %Y")}: #{index}</span>
        <p class="script-title">{script.title}</p>

        <ul class="script-tags">
{audience_tag}
{tags}
{htmlify_wordcount(script.words)}
</ul>

{htmlify_series_data(script.series)}

        <blockquote class="script-summary">
{summary}
        </blockquote>

<span><b>Links:</b></span> {script_links}

{htmlify_fills_summary(script.fills, attendant_va=script.attendant_va)}
    </div>
"""


def load_scripts() -> list[Script]:
    """Return a list of the scripts loaded from the file."""
    datafile = Path(__file__).parent.parent / "script-data.json"
    scripts = parse(datafile)

    # filter to only published scripts
    scripts = [s for s in scripts if s.published is not None and s.published <= datetime.today()]
    return sorted(scripts, key=attrgetter("published"), reverse=True)


def scripts_tab(scripts: list[Script]) -> str:
    """Create the scripts tab"""
    s = StringIO()

    s.write("""<div id="_scripts" class="all-scripts tabcontent">""")
    
    for index, script in reverse_enumerate(scripts):
        if script.published is None:
            # skip any scripts which aren't published
            continue

        s.write(htmlify(script, index=index))
    s.write("""</div>""")

    return s.getvalue()


def build_index(scripts: list[Script]):
    total_scripts = len(scripts)
    total_fills = sum(s.num_fills for s in scripts)

    # get overall data for filters
    series_names: set[str] = set()
    audience_tags: set[str] = set()
    all_VAs: set[str] = set()

    for script in scripts:
        if (s := script.series) is not None:
            series_names.add(s.title)

        for tag in script.audience:
            audience_tags.add(tag)

        all_VAs |= script.filled_by

    filter_section = html_filter_section(
        num_scripts=total_scripts,
        num_fills=total_fills,
        series_names=series_names,
        audience_tags=audience_tags,
        filled_by=all_VAs,
    )

    outpath = Path(__file__).parent.parent / "index.html"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html_header())
        f.write(introduction())
        f.write(filter_section)

        #         f.write("""\
        #     <div class="tab">
        #         <button class="tablink" onclick="openTab(event, '_scripts');">Scripts</button>
        #         <button class="tablink" onclick="openTab(event, '_audios');">Audios</button>
        #         <button class="tablink" onclick="openTab(event, '_filldata');">Fill Data</button>
        #     </div>
        # """)

        f.write(scripts_tab(scripts))

        f.write(html_closer())


def build_fills_page(scripts: list[Script]) -> None:
    nsfw_scripts = set(script.title for script in scripts if is_nsfw(script))

    fills: list[FillData] = []
    for script in scripts:
        fills.extend(script.fills)

    fills.sort(key=lambda fill: fill.date, reverse=True)
    s = StringIO()

    s.write(html_header())
    s.write(introduction_fills_page())
    s.write("""<div class="all-scripts">""")

    for i, fill in reverse_enumerate(fills):
        creators = ", ".join(fill.creators)
        date = fill.date.strftime("%d %b %Y")
        links = "\n".join(
            f"""<li>{make_link_icon(label)} <a href="{href}">{label}</a></li>""" for
            label, href in fill.links.items())

        extra = "blurred" if fill.script in nsfw_scripts else ""

        s.write(f"""\
<div class="container fill-{summarise_gender(fill.audience)} {extra}">
    <p>#{i:,} | {date}</p>
    
    <p style="font-weight: bold;">{creators}</p>
    
    <p>{fill.title}</p>
    
    <p style="font-style: italic; font-size: 80%;">{make_link_icon("scriptbin")} {fill.script}</p>
    
        <ul>
            {links}
        </ul>
</div>
""")

    s.write("""</div></body>""")

    outpath = Path(__file__).parent.parent / "all-fills.html"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(s.getvalue())


def main():
    scripts = load_scripts()
    build_index(scripts)
    build_fills_page(scripts)


if __name__ == "__main__":
    main()
