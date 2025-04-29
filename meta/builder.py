from __future__ import annotations

import json
import re
from collections.abc import Collection, Iterable, Iterator
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from operator import attrgetter
from pathlib import Path
from typing import Self

import jinja2

from build_icons import get_link_icon_classes
from custom_filters import add_all_filters, any_nsfw
from parser import FillData, Script, ScriptFingerprint, SeriesData, WordCountData, parse


def reverse_enumerate[T](seq: Collection[T], *, start: int = 1) -> Iterator[tuple[int, T]]:
    """Return an enumeration of (index, item), but numbered n, n-1, ..., 1"""
    n = len(seq)
    for i, item in zip(range(n + (start - 1), start - 1, -1), seq):
        yield i, item


def count_speakers(audience_tag: str) -> int:
    """Determine the number of speakers specified in the audience tag."""
    matches = re.findall(r"TM|TF|TA|NB|M|F|A", audience_tag.split("4")[0])
    return len(matches)


def load_scripts() -> list[Script]:
    """Return a list of the scripts loaded from the file."""
    datafile = Path(__file__).parent.parent / "script-data.json"
    scripts = parse(datafile)

    # filter to only published scripts
    scripts = [s for s in scripts if s.published is not None and s.published <= datetime.today()]
    return sorted(scripts, key=attrgetter("published"), reverse=True)


def load_audios() -> list[EFillData]:
    datafile = Path(__file__).parent.parent / "script-data.json"
    data = json.loads(datafile.read_text(encoding="utf-8"))

    fills = [FillData.from_dict(fill) for fill in data["audios"]]
    return [EFillData.from_fill_data(f) for f in fills]


@dataclass
class ELinkData:
    href: str
    label: str
    icons: str = field(init=False)

    def __post_init__(self):
        self.icons = " ".join(get_link_icon_classes(self.label))


@dataclass
class EFillData:
    creators: list[str]
    title: str
    audience: str
    date: date
    duration: timedelta | None
    links: list[ELinkData]
    label: str | None
    script: ScriptFingerprint
    index: int | None = None
    additional_classes: list[str] = field(default_factory=list)
    embed: str | None = field(init=False)

    def __post_init__(self):
        if (match := re.search(r"youtube\.com/watch\?v=([^&]+)|youtu\.be/([^&]+)", self.links[0].href)):
            self.embed = f"https://www.youtube.com/embed/{match.group(1) if match.group(1) else match.group(2)}"
        else:
            self.embed = None

    @classmethod
    def from_fill_data(cls, data: FillData, *, index: int | None = None,
                       additional_classes: list[str] | None = None) -> Self:
        if additional_classes is None:
            additional_classes = []

        links = [ELinkData(href=href, label=label) for label, href in data.links.items() if href]

        assert data.date is not None

        return cls(
            creators=data.creators,
            title=data.title,
            audience=data.audience,
            date=data.date.date(),
            duration=data.duration,
            links=links,
            label=data.label,
            index=index,
            script=data.script,
            additional_classes=additional_classes
        )


@dataclass
class ESeriesData:
    title: str
    index: int

    @classmethod
    def from_series_data(cls, data: SeriesData) -> Self:
        return cls(
            title=data.title,
            index=data.index
        )


@dataclass
class EScriptData:
    index: int
    title: str
    series: ESeriesData | None
    audience_tags: list[str]
    content_tags: list[str]
    wordcount_tag: str
    summary: str
    links: list[ELinkData]
    published: date | None
    fills: list[EFillData]
    attendant_va: list[str] | None


@dataclass
class ScriptContext:
    num_scripts: int
    num_fills: int
    series_options: list[str] = field(default_factory=list)
    speaker_count_options: list[int] = field(default_factory=list)
    audience_tags: list[str] = field(default_factory=list)
    filled_by: list[str] = field(default_factory=list)
    scripts: list[EScriptData] = field(default_factory=list)

    @classmethod
    def from_scripts(cls, scripts: list[Script]):
        return cls(
            num_scripts=len(scripts),
            num_fills=sum(s.num_fills for s in scripts),
            series_options=get_series_options(scripts),
            speaker_count_options=get_number_of_speakers(scripts),
            audience_tags=get_audience_tags(scripts),
            filled_by=get_filled_by(scripts),
            scripts=make_script_data(scripts)
        )


@dataclass
class AudioContext:
    num_audios: int
    audios: list[EFillData] = field(default_factory=list)

    @classmethod
    def from_audios(cls, audios: list[EFillData]):
        return cls(
            num_audios=len(audios),
            audios=audios
        )


def get_series_options(scripts: Iterable[Script]) -> list[str]:
    """Get a list of all of the different series across the different scripts, including any and one-shot categories."""
    series = set(script.series.title for script in scripts if script.series is not None)
    return ["", "(one-shots only)", *sorted(series, key=str.lower)]


def get_audience_tags(scripts: Iterable[Script]) -> list[str]:
    """Get a sorted list of all audience tags across the different scripts."""
    options: set[str] = set()

    for script in scripts:
        options |= set(tag.upper() for tag in script.audience)

    return sorted(options)


def get_number_of_speakers(scripts: Iterable[Script]) -> list[int]:
    """Get a sorted list of all numbers of speakers across the different scripts."""
    options: set[int] = set()

    for script in scripts:
        for audience in script.audience:
            speakers = count_speakers(audience)
            options.add(speakers)

    return sorted(options)


def get_filled_by(scripts: Iterable[Script]) -> list[str]:
    """Get a sorted list of all VAs who have filled any of the scripts."""
    options: set[str] = set()

    for script in scripts:
        options |= script.filled_by

    return ["", *sorted(options, key=str.lower)]


def make_wordcount_tag(words: WordCountData) -> str:
    """Return the inner HTML content corresponding to the given word count data"""
    num_speakers = len(words.spoken.keys())
    full = words.all_spoken

    if not num_speakers:
        raise ValueError(f"invalid speaker count: {words}")

    if num_speakers == 1:
        return f"{full:,} words"

    individuals = "+".join(format(v, ",") for v in words.spoken.values())
    return f"{individuals} (={full:,} words)"


def _make_script_data(i: int, script: Script) -> EScriptData:
    links = [ELinkData(href=href, label=label) for label, href in script.links.combine_dict().items() if href]
    fills = [EFillData.from_fill_data(data=fill) for fill in script.fills]

    series = ESeriesData.from_series_data(script.series) if script.series else None
    return EScriptData(
        index=i,
        title=script.title,
        audience_tags=script.audience,
        content_tags=script.tags,
        wordcount_tag=make_wordcount_tag(script.words),
        summary=script.summary,
        links=links,
        published=script.published,
        fills=fills,
        series=series,
        attendant_va=script.attendant_va
    )


def make_script_data(scripts: list[Script]) -> list[EScriptData]:
    return [_make_script_data(i, script) for i, script in reverse_enumerate(scripts)]


def make_fill_data(scripts: list[Script]) -> list[EFillData]:
    fills: list[EFillData] = []

    for script in scripts:
        for fill in script.fills:
            additional_classes = ["blurred"] if any_nsfw(script.tags) else []
            e = EFillData.from_fill_data(fill, additional_classes=additional_classes)
            fills.append(e)

    fills.sort(key=lambda fill: fill.date, reverse=True)

    # fix the indexing
    for i, efill in reverse_enumerate(fills):
        efill.index = i

    return fills


def build_index(scripts: list[Script], template_dir: Path, output_file: Path) -> None:
    """Write a new index.html"""
    context = ScriptContext.from_scripts(scripts=scripts)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=jinja2.select_autoescape(),
    )
    add_all_filters(env)

    template = env.get_template("index.html")
    html = template.render(**asdict(context))

    with open(output_file, mode="w", encoding="utf-8") as f:
        f.write(html)


def build_audios(audios: list[EFillData], template_dir: Path, output_file: Path) -> None:
    """Write a new audios.html"""
    context = AudioContext.from_audios(audios=audios)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=jinja2.select_autoescape(),
    )
    add_all_filters(env)

    template = env.get_template("audios.html")
    html = template.render(**asdict(context))

    with open(output_file, mode="w", encoding="utf-8") as f:
        f.write(html)


def build_all_fills(scripts: list[Script], template_dir: Path, output_file: Path) -> None:
    """Write a new all-fills.html"""
    fills = make_fill_data(scripts)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=jinja2.select_autoescape(),
    )
    add_all_filters(env)

    template = env.get_template("all-fills.html")
    html = template.render(fills=fills)

    with open(output_file, mode="w", encoding="utf-8") as f:
        f.write(html)


def main():
    root = Path(__file__).parent.parent
    template_root = root / "meta" / "templates"

    scripts = load_scripts()
    audios = load_audios()

    build_index(scripts, template_dir=template_root / "index", output_file=root / "index.html")
    # build_audios(audios, template_dir=template_root / "audios", output_file=root / "audios.html")
    build_all_fills(scripts, template_dir=template_root / "fills", output_file=root / "all-fills.html")


if __name__ == "__main__":
    main()
