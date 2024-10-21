import json
from pathlib import Path
from typing import Any

import yaml


def load_data(datafile: Path) -> list[dict[str, Any]]:
    with open(datafile, "r", encoding="utf-8") as f:
        data: dict[str, list[dict[str, Any]]] = yaml.safe_load(f)

    result: list[dict[str, Any]] = []

    for script in data["scripts"]:
        # remove any script which isn't published
        if script.get("published") is None:
            continue

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


def main():
    in_file = Path(__file__).parent.parent / "script-data.yaml"
    out_file = Path(__file__).parent.parent / "script-data.json"

    data = {"scripts": load_data(in_file)}

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    main()
