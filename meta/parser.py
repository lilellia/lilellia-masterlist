import re
from dataclasses import dataclass, field
import dateparser
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Any, Self


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


@dataclass
class FillData:
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

        return cls(**data, duration=duration, date=date)


@dataclass
class Script:
    title: str
    audience: list[str]
    tags: list[str]
    series: SeriesData | None
    summary: str
    words: WordCountData
    finished: datetime | None
    published: datetime | None
    links: LinkData
    attendant_va: str | None = None
    fills: list[FillData] = field(default_factory=list)
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
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

        fills = data.pop("fills", [])
        fills = [FillData.from_dict(f) for f in fills]

        links = data.pop("links", None)
        if links:
            links = LinkData(**links)

        attendant_va = data.pop("attendant VA", None)

        return cls(
            **data,
            series=series,
            words=words,
            finished=finished,
            published=published,
            fills=fills,
            links=links,
            attendant_va=attendant_va,
        )

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
