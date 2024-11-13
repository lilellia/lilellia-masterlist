from argparse import ArgumentParser
from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

import yaml


def load_data(datafile: Path) -> list[dict[str, Any]]:
    with open(datafile, "r", encoding="utf-8") as f:
        data: dict[str, list[dict[str, Any]]] = yaml.safe_load(f)

    result: list[dict[str, Any]] = []

    for script in data["scripts"]:
        if script.get("published") is not None:
            script["published"] = script["published"].strftime("%Y-%m-%d")

        if dt := script.get("finished"):
            script["finished"] = dt.strftime("%Y-%m-%d")

        # remove credited, informed, and notes keys from fills
        keys_to_remove = ("credited", "informed", "notes")

        fill: dict[str, Any]
        for fill in script.get("fills", []):
            for key in keys_to_remove:
                fill.pop(key, None)

            if dt := fill.get("date"):
                fill["date"] = dt.strftime("%Y-%m-%d")

        result.append(script)

    return result


def remove_unpublished(data: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(x) for x in data if x.get("published") is not None]


def main():
    parser = ArgumentParser()
    parser.add_argument("-i", "-y", "--in-file", type=Path, help="the source .yaml file to read", required=True)
    parser.add_argument("-o", "--out-file", type=Path, help="the output .json file", required=True)
    parser.add_argument("-p", "--private", type=Path, help="the output path for the private .json file")
    args = parser.parse_args()

    # read the source data
    all_scripts = load_data(args.in_file)
    public_scripts = remove_unpublished(all_scripts)

    # output the data to file
    with open(args.out_file, "w", encoding="utf-8") as f:
        json.dump({"scripts": public_scripts}, f, indent=4)

    if args.private is None:
        args.private = args.out_file.with_stem(f"{args.out_file.stem}-private")

    with open(args.private, "w", encoding="utf-8") as f:
        json.dump({"scripts": all_scripts}, f, indent=4)


if __name__ == "__main__":
    main()
