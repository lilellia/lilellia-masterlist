import re
from parser import FillData, Script, parse
from pathlib import Path


def html_header(num_scripts: int, num_fills: int) -> str:
    return f"""\
<html>
<head>
    <meta charset="utf-8">
    <title>lilellia's masterlist</title>
    <link href="static/css/main.css" rel="stylesheet">
</head>
<body>
    <h1>lilellia's masterlist</h1>
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


def htmlify_fill(fill: FillData) -> str:
    if re.match(r"^M+4", fill.audience):
        gender = "male"
    elif re.match(r"^F+4", fill.audience):
        gender = "female"
    else:
        gender = "mixed"

    link = extract_fill_link(fill)

    return f"""\
        <li class="fill-{gender}">
            <a href="{link}">{fill.creator}</a>
        </li>
"""


def htmlify(script: Script) -> str:
    link_repl = {"google_docs": "Google Docs"}

    date_tag = f"""\t\t\t<li class="script-tag date-tag">{script.published.strftime("%d %b %Y")}</li>"""
    audience_tag = "\n".join(
        f"""\t\t\t<li class="script-tag audience-tag {atag.lower()}">{atag.upper()}</li>"""
        for atag in script.audience
    )
    tags = "\n".join(
        f"""\t\t\t<li class="script-tag">{tag}</li>""" for tag in script.tags
    )

    script_links = "\n".join(
        f"""\t\t\t<li class="script-link"><a href="{href}">{link_repl.get(label, label)}</a></li>"""
        for label, href in script.links.script.items()
    )

    post_links = "\n".join(
        f"""\t\t\t<li class="post-link"><a href="{href}">{re.sub(r"^r_", "r/", label)}</a></li>"""
        for label, href in script.links.post.items()
    )

    fills = "\n".join(htmlify_fill(f) for f in script.fills)

    return f"""\
    <div class="script-data">
        <p class="script-title">{script.title}</p>

        <ul class="script-tags">
            {date_tag}
            {audience_tag}
            {tags}
        </ul>

        <blockquote class="script-summary">
            {script.summary}
        </blockquote>
        
        <ul class="script-links">
            {script_links}
            {post_links}
        </ul>

        <div>
        <b>Fills ({script.num_fills}):</b>
        <ul class="script-fills">
            {fills}
        </ul>
        </div>
    </div>
"""


def main():
    datafile = Path(__file__).parent.parent / "script-data.yaml"
    scripts = parse(datafile)

    total_scripts = len(scripts)
    total_fills = sum(s.num_fills for s in scripts)

    outpath = Path(__file__).parent.parent / "index.html"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html_header(num_scripts=total_scripts, num_fills=total_fills))

        for script in scripts:
            f.write(htmlify(script))

        f.write(html_closer())


if __name__ == "__main__":
    main()
