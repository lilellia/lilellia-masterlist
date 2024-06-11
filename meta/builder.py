from datetime import datetime
from io import StringIO
import re
from operator import attrgetter
from parser import FillData, Script, SeriesData, WordCountData, parse
from pathlib import Path
from typing import Any, Iterable, Literal

# a set containing tags that designate the script as NSFW
NSFW_TAGS = {"18+", "nsfw", "r18"}


LINK_ICONS = {
    "YouTube": ("fa-brands", "fa-youtube"),
    "soundgasm": ("fa-solid", "fa-headphones"),
    "Patreon": ("fa-brands", "fa-patreon"),
    "Reddit": ("fa-brands", "fa-reddit-alien"),
    "Google Docs": ("fa-brands", "fa-google-drive"),
    "scriptbin": ("fa-solid", "fa-file-lines")
}



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
    <link rel="icon" type="image/x-icon" href="/static/favicon.png">
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
    return """\
<body>
    <h1>lilellia's masterlist</h1>

    <div class="container terms-of-use">
        <div class="greeting">
            <p>Hi, I'm <span class="lilellia">lilellia</span>, the butterfly princess of hugs! Welcome to my masterlist!</p>
            <p>I mostly write cute, domestic/fluff, a bit of romance (established or friends-to-lovers), usually F4F/F4A</p>
            <p class="butterfly">∼ ʚїɞ ∼</p>
        </div>

        <h2>Terms of Script Use</h2>
        <ul>
            <li class="terms-of-use"><b>Usage:</b> All of my scripts are freely available for use. Please credit me (<a href="https://reddit.com/user/lilellia">u/lilellia</a> and/or @lilellia) if you use the script, and let me know—I'd love to see what you come up with! Feel free to monetise it (but DM me first if you want to post on Patreon, etc.).</li>
            <li class="terms-of-use"><b>Editing:</b> Small changes to the scripts are okay, but please ask before making any major line changes, additions, deletions, gender swaps, etc. Vocal cues and sound effects are suggestions, so feel free to be creative with those!</li>
            <li class="terms-of-use"><b>Other notes:</b> I find it easier to write the listener's dialogue rather than keep track of half of a conversation, so their lines are given for context but aren't meant to be voiced. The word counts given only include the spoken text.</li>
        </ul>

        <div>
            <p class="butterfly">∼ ʚїɞ ∼</p>
            <p>NSFW scripts are blurred. Click them to reveal the contents.</p>
        </div>
    </div>
"""


def html_filter_section(
    num_scripts: int,
    num_fills: int,
    series_names: Iterable[str],
    audience_tags: Iterable[str],
    filled_by: Iterable[str],
) -> str:
    series = "\n".join(
        f"""\t\t\t<option class="{serialise(name)}" value="{name}">{name}</option>"""
        for name in sorted(series_names)
    )

    audience = "\n".join(f"""\t\t\t<option value="{tag}">{tag}</option>""" for tag in sorted(audience_tags))
    filled_by = "\n".join(
        f"""\t\t\t<option value="{name}">{name}</option>"""
        for name in sorted(filled_by, key=str.lower)  # make sort case-insensitive
    )

    return f"""\
    <div class="search-and-filter">
        <p><span id="numScripts">{num_scripts:,}</span>/{num_scripts:,} scripts・<span id="numFills">{num_fills:,}</span>/{num_fills:,} fills</p>


        <table>
        <tr>
        <td colspan="2">
            
        <input type="text" id="filterInput" onkeyup="filterScripts()" placeholder="filter by title/summary..."><br/>
        </td>
        </tr>

        <tr>
        <td><label for="seriesFilter">Filter by Series:</label></td>
        <td><select name="seriesFilter" id="seriesFilter" onchange="filterScripts()">
            <option value=""></option>
            <option value="(one-shots only)">(one-shots only)</option>
{series}
        </select>
        </td>
        </tr>

        <tr>
        <td><label for="audienceTagFilter">Filter by Audience Tag:</label></td>
        <td><select name="audienceTagFilter" id="audienceTagFilter" onchange="filterScripts()">
            <option value=""></option>
{audience}
        </select>
        </td>
        </tr>

        <tr>
        <td><label for="unfilledOnlyFilter">Show unfilled scripts only?</label></td>
        <td><select name="unfilledOnlyFilter" id="unfilledOnlyFilter" onchange="filterScripts()">
            <option value="no">no (show all scripts)</option>
            <option value="yes">yes (show only unfilled scripts)</option>
        </select>
        </td>
        </tr>
    
        <tr>
        <td><label for="filledByFilter">Filter by VAs:</label></td>
        <td><select name="filledByFilter" id="filledByFilter" onchange="filterScripts()">
            <option value=""></option>
{filled_by}
        </select>
        </td>
        </tr>
    
        </table>

    </div>
"""


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


def icon(*fa_classes: str, direction: Literal["left", "right"]) -> str:
    """Create a font awesome icon."""
    class_str = " ".join(fa_classes)
    return f"""<i class="icon-{direction} {class_str}"></i>"""


def htmlify_fill(fill: FillData, *, attendant_va: str | None) -> str:
    priority_link = extract_priority_fill_link(fill)
    label = f" [{fill.label}]" if fill.label else ""
    attendant = (
        icon("fa-solid", "fa-star", direction="right")
        if attendant_va and attendant_va in fill.creators
        else ""
    )
    self_fill = icon("fa-solid", "fa-crown", direction="right") if "lilellia" in fill.creators else ""

    creators = ", ".join(fill.creators)

    tag_class = f"fill-{summarise_gender(fill.audience)}"
    tag_label = f"""<a href="{priority_link}">{creators}</a>{label}{attendant}{self_fill}"""
    return links_to_tag(fill.links, tag_class=tag_class, tag_label=tag_label)


def htmlify_fills_summary(fills: list[FillData], *, attendant_va: str | None) -> str:
    if not fills:
        return ""

    fill_tags = "\n".join(htmlify_fill(f, attendant_va=attendant_va) for f in fills)
    return f"""\
        <div class="fill-summary">
            <p><b>Fills (<span class="fill-count">{len(fills)}</span>):</b></p>
            <ul class="script-fills">
{fill_tags}
            </ul>
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
    return text.lower().replace(" ", "-").replace("'", "").replace('"', "")


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


def links_to_tag(links: dict[str, str], tag_class: str, tag_label: str) -> str:
    """Convert a dict of {label: href} to a tooltip list of <a> tags"""
    def get_icon_classes(label: str) -> tuple[str, ...]:
        if label.startswith("r/"):
            return LINK_ICONS["Reddit"]

        return LINK_ICONS.get(label, ("",))

    lis = [f"""<li>{icon(*get_icon_classes(label), direction="left")} <a href="{href}">{label}</a></li>""" for label, href in links.items()]
    li_string = "\n".join(lis)
    return f"""
    <li class="{tag_class}">
		<div class="tooltip">
		    {tag_label}
			<div class="tooltiptext">
				<ul>
					{li_string}
				</ul>
			</div>
		</div>
	</li>
"""

def htmlify(script: Script) -> str:
    # handle all the "content" tags
    assert script.published is not None
    date_tag = f"""\t\t\t<li class="script-tag meta-tag">{script.published.strftime("%d %b %Y")}</li>"""
    audience_tag = "\n".join(
        f"""\t\t\t<li class="script-tag audience-tag {atag.lower()}">{atag.upper()}</li>"""
        for atag in script.audience
    )
    tags = "\n".join(f"""\t\t\t<li class="{script_tag_classes(tag)}">{tag}</li>""" for tag in script.tags)

    summary = "\n".join(f"\t\t\t<p>{par}</p>" for par in script.summary.splitlines())

    classes = ["container", "script-data"]
    if is_nsfw(script):
        classes.append("blurred")

    return f"""\
    <div class="{' '.join(classes)}" id={serialise(script.title)}>
        <p class="script-title">{script.title}</p>

        <ul class="script-tags">
{date_tag}
{audience_tag}
{tags}
{htmlify_wordcount(script.words)}
{links_to_tag(script.links.script, tag_class="link-tag", tag_label="script links")}
{links_to_tag(script.links.post, tag_class="link-tag", tag_label="post links")}
</ul>

{htmlify_series_data(script.series)}

        <blockquote class="script-summary">
{summary}
        </blockquote>

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
    for script in scripts:
        if script.published is None:
            # skip any scripts which aren't published
            continue

        s.write(htmlify(script))
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
    fills: list[FillData] = []
    for script in scripts:
        fills.extend(script.fills)

    fills.sort(key=lambda fill: fill.date)
    s = StringIO()

    s.write(html_header())
    s.write("""<table>""")
    s.write("""\
    <tr>
        <th></th>
        <th>Date</th>
        <th>Script</th>
        <th>Creators</th>
        <th>Link</th>
    </tr>
 """)

    for i, fill in enumerate(fills, start=1):
        date = fill.date.strftime("%d %b %Y") if fill.date else ""
        creators = ", ".join(fill.creators)
        link = extract_priority_fill_link(fill)
        
        
        s.write(f"""\
    <tr>
        <td>{i:,}</td>
        <td>{date}</td>
        <td>---</td>
        <td>{creators}</td>
        <td><a href="{link}">{fill.title}</a></td>
""")

    s.write("""</table>""")

    
    outpath = Path(__file__).parent.parent / "all-fills.html"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(s.getvalue())



def main():
    scripts = load_scripts()
    build_index(scripts)
    build_fills_page(scripts)


if __name__ == "__main__":
    main()
