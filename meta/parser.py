from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Self

import dateparser


@dataclass
class SeriesData:
    title: str
    index: int


@dataclass
class WordCountData:
    spoken: dict[str, int]
    total: int

    @property
    def all_spoken(self) -> int:
        """Return the total number of words spoken."""
        return sum(self.spoken.values())


@dataclass
class LinkData:
    script: dict[str, str]
    post: dict[str, str]

    def combine_dict(self) -> dict[str, str]:
        return {**self.script, **self.post}

    @property
    def canonical_link(self) -> str:
        key = list(self.post.keys())[0]
        return self.post[key]

@dataclass
class FillData:
    script: ScriptFingerprint
    creators: list[str]
    title: str
    audience: str
    links: dict[str, str]
    date: datetime | None
    duration: timedelta | None
    label: str | None = None

    @staticmethod
    def parse_duration(duration_str: str) -> timedelta:
        match = re.match(r"(?P<hours>\d+h)?(?P<minutes>\d+m)(?P<seconds>\d+s)", duration_str)

        if not match:
            raise ValueError(f"invalid duration value: {duration_str!r}")

        if match.group("hours"):
            hours = match.group("hours").rstrip("h")
        else:
            hours = 0

        minutes = match.group("minutes").rstrip("m")
        seconds = match.group("seconds").rstrip("s")

        return timedelta(hours=int(hours), minutes=int(minutes), seconds=float(seconds))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        # process duration value
        duration_str = data.pop("duration", "")
        duration = cls.parse_duration(duration_str)

        # process date value
        date_str = data.pop("date", "")
        date = dateparser.parse(date_str)

        # make fingerprint
        if isinstance(data["script"], dict):
            data["script"] = ScriptFingerprint(
                title=data["script"]["title"],
                authors=data["script"].get("authors", ["lilellia"]),
                canonical_link=data["script"]["link"],
            )

        return cls(**data, duration=duration, date=date)


@dataclass
class ScriptFingerprint:
    title: str
    authors: list[str]
    canonical_link: str


@dataclass
class Script:
    title: str
    authors: list[str]
    audience: list[str]
    tags: list[str]
    series: SeriesData | None
    summary: str
    words: WordCountData
    finished: datetime | None
    published: datetime | None
    links: LinkData
    attendant_va: list[str] | None = None
    fills: list[FillData] = field(default_factory=list)
    notes: str | None = None

    @property
    def fingerprint(self) -> ScriptFingerprint:
        return ScriptFingerprint(
            title=self.title,
            authors=self.authors,
            canonical_link=self.links.canonical_link,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        authors = data.pop("authors", ["lilellia"])

        series = data.pop("series", None)
        if series:
            series = SeriesData(**series)

        words = data.pop("words", None)
        if words:
            words = WordCountData(**words)

        finished = data.pop("finished", None)
        if finished:
            finished = dateparser.parse(finished)

        published = data.pop("published", None)
        if published:
            published = dateparser.parse(published)

        links = data.pop("links", None)
        if links:
            links = LinkData(**links)

        fingerprint = ScriptFingerprint(
            title=data["title"],
            authors=data.get("authors", ["lilellia"]),
            canonical_link=links.canonical_link,
        )

        fill_data: list[dict[str, Any]] = data.pop("fills", [])
        fills: list[FillData] = []
        for f in fill_data:
            fills.append(FillData.from_dict({"script": fingerprint, **f}))

        attendant_va = data.pop("attendant VA", None)

        return cls(
            **data,
            authors=authors,
            series=series,
            words=words,
            finished=finished,
            published=published,
            fills=fills,
            links=links,
            attendant_va=attendant_va,
        )

    @property
    def speakers(self) -> tuple[str, ...]:
        """Return a tuple of the speaker names in the script."""
        return tuple(self.words.spoken.keys())

    @property
    def spoken_words(self) -> int:
        """Return the total number of spoken words in the script."""
        return self.words.all_spoken

    @property
    def speech_density(self) -> float:
        """Return the density of speech in the script."""
        return self.words.all_spoken / self.words.total

    @property
    def num_fills(self) -> int:
        """Return the number of known fills for this script."""
        return len(self.fills)

    @property
    def filled_by(self) -> set[str]:
        """Return a set of the VAs who have filled this script."""
        creators: set[str] = set()

        for f in self.fills:
            creators |= set(f.creators)

        return creators


def parse(filepath: Path) -> list[Script]:
    with open(filepath, mode="r", encoding="utf-8") as f:
        data = json.load(f)

    return [Script.from_dict(item) for item in data["scripts"]]
