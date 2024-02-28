import re
from parser import FillData, Script, SeriesData, WordCountData, parse
from pathlib import Path


def html_header(num_scripts: int, num_fills: int) -> str:
    return f"""\
<html>
<head>
    <meta charset="utf-8">
    <title>lilellia's masterlist</title>
    <link href="static/css/main.css" rel="stylesheet">
    <link href="static/css/series.css" rel="stylesheet">
    <script type="text/javascript" src="static/js/filter.js"></script>
</head>
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
    </div>

    <div class="search-and-filter">
        <p><span id="numScripts">{num_scripts:,}</span>/{num_scripts:,} scripts・<span id="numFills">{num_fills:,}</span>/{num_fills:,} fills</p>

        <input type="text" id="filterInput" onkeyup="filterScripts()" placeholder="filter by title/summary..."><br/>

        <input type="checkbox" id="unfilledScripts" name="unfilledScripts" onclick="filterScripts()">
        <label for="unfilledScripts">Show only unfilled scripts?</label><br/>

        <input type="checkbox" id="oneShots" name="oneShots" onclick="filterScripts()">
        <label for="oneShots">Show only one-shot scripts?</label>
    </div>
"""


def html_closer() -> str:
    return """\
</body>
</html>
"""


def extract_fill_link(fill: FillData) -> str:
    youtube = fill.links.get("YouTube")
    soundgasm = fill.links.get("soundgasm")

    link = youtube or soundgasm
    if link is None:
        raise ValueError(f"could not find link for fill: {fill.title}")

    return link


def summarise_gender(audience: str) -> str:
    if re.match(r"^M+4", audience):
        gender = "male"
    elif re.match(r"^F+4", audience):
        gender = "female"
    else:
        gender = "mixed"

    return gender


def htmlify_fill(fill: FillData, *, attendant_va: str | None) -> str:
    link = extract_fill_link(fill)
    label = f" [{fill.label}]" if fill.label else ""
    attendant = " [※]" if attendant_va and fill.creator == attendant_va else ""

    return f"""\t\t\t\t<li class="fill-{summarise_gender(fill.audience)}"><a href="{link}">{fill.creator}</a>{label}{attendant}</li>"""


def htmlify_fills_summary(fills: list[FillData], *, attendant_va: str | None) -> str:
    if not fills:
        return ""

    fill_tags = "\n".join(htmlify_fill(f, attendant_va=attendant_va) for f in fills)
    return f"""\
        <div class="fill-summary">
            <b>Fills (<span class="fill-count">{len(fills)}</span>):</b>
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

    nsfw_tags = ["18+", "nsfw", "r18"]
    if tag in nsfw_tags:
        classes.append("nsfw-tag")

    return " ".join(classes)


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

    return f"""\t\t\t<li class="script-tag meta-tag">{content} words</li>"""


def htmlify(script: Script) -> str:
    # handle all the "content" tags
    assert script.published is not None
    date_tag = f"""\t\t\t<li class="script-tag meta-tag">{script.published.strftime("%d %b %Y")}</li>"""
    audience_tag = "\n".join(
        f"""\t\t\t<li class="script-tag audience-tag {atag.lower()}">{atag.upper()}</li>"""
        for atag in script.audience
    )
    tags = "\n".join(
        f"""\t\t\t<li class="{script_tag_classes(tag)}">{tag}</li>"""
        for tag in script.tags
    )

    # handle links
    script_links = "\n".join(
        f"""\t\t\t<li class="script-link"><a href="{href}">{label}</a></li>"""
        for label, href in script.links.script.items()
    )

    post_links = "\n".join(
        f"""\t\t\t<li class="post-link"><a href="{href}">{re.sub(r"^r_", "r/", label)}</a></li>"""
        for label, href in script.links.post.items()
    )

    summary = "\n".join(f"\t\t\t<p>{par}</p>" for par in script.summary.splitlines())

    return f"""\
    <div class="container script-data" id={serialise(script.title)}>
        <p class="script-title">{script.title}</p>

        <ul class="script-tags">
{date_tag}
{audience_tag}
{tags}
{htmlify_wordcount(script.words)}
        </ul>

{htmlify_series_data(script.series)}

        <blockquote class="script-summary">
{summary}
        </blockquote>
        
        <ul class="script-links">
{script_links}
{post_links}
        </ul>

{htmlify_fills_summary(script.fills, attendant_va=script.attendant_va)}
    </div>
"""


def main():
    datafile = Path(__file__).parent.parent / "script-data.yaml"
    scripts = parse(datafile)

    # filter to only published scripts
    scripts = [s for s in scripts if s.published is not None]

    total_scripts = len(scripts)
    total_fills = sum(s.num_fills for s in scripts)

    outpath = Path(__file__).parent.parent / "index.html"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html_header(num_scripts=total_scripts, num_fills=total_fills))

        for script in scripts:
            if script.published is None:
                # skip any scripts which aren't published!
                continue

            f.write(htmlify(script))

        f.write(html_closer())


if __name__ == "__main__":
    main()
