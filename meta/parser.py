import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Self

import yaml


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
    creator: str
    title: str
    audience: str
    links: dict[str, str]
    date: datetime
    duration: timedelta
    credited: bool
    informed: bool
    label: str | None = None
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        duration = data.pop("duration")

        match = re.match(
            r"(?P<hours>\d+h)?(?P<minutes>\d+m)(?P<seconds>\d+s)", duration
        )

        if not match:
            raise ValueError(f"invalid duration value: {duration!r}")

        if match.group("hours"):
            hours = match.group("hours").rstrip("h")
        else:
            hours = 0

        minutes = match.group("minutes").rstrip("m")
        seconds = match.group("seconds").rstrip("s")

        duration = timedelta(
            hours=int(hours), minutes=int(minutes), seconds=float(seconds)
        )

        return cls(**data, duration=duration)


@dataclass
class Script:
    title: str
    audience: list[str]
    tags: list[str]
    series: SeriesData | None
    summary: str
    words: WordCountData
    finished: str
    published: str
    links: LinkData
    attendant_va: str | None = None
    fills: list[FillData] = field(default_factory=list)
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        series = data.pop("series")
        if series:
            series = SeriesData(**series)

        words = data.pop("words")
        words = WordCountData(**words)

        fills = data.pop("fills")
        fills = [FillData.from_dict(f) for f in fills]

        links = data.pop("links")
        links = LinkData(**links)

        return cls(**data, series=series, words=words, fills=fills, links=links)

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


def parse(filepath: Path) -> list[Script]:
    with open(filepath, mode="r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return [Script.from_dict(item) for item in data["scripts"]]
