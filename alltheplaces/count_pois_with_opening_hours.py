# SPDX-FileCopyrightText: 2025 Sascha Brawer <sascha@brawer.ch>
# SPDX-License-Identifier: MIT
#
# Count how many POIs in AllThePlaces.xyz have opening hours, by country.
#
# Usage:
#
#     wget https://alltheplaces-data.openaddresses.io/runs/2025-12-06-13-33-06/output.zip
#     python3 count_pois_with_opening_hours.py output.zip
#
# Most recent path to output.zip is on https://alltheplaces.xyz/

from collections import Counter
import json
from pathlib import Path
import sys
from zipfile import ZipFile


def count_pois_with_opening_hours(path: Path) -> Counter:
    counter = Counter()
    with ZipFile(path, "r") as zf:
        for filename in sorted(zf.namelist()):
            if not filename.endswith(".geojson"):
                continue
            with zf.open(filename) as f:
                data = f.read()
                if not data:
                    continue
                try:
                    collection = json.loads(data)
                except json.decoder.JSONDecodeError:
                    print(f"cannot decode json: {filename}")
                    continue
            for feature in collection["features"]:
                props = feature["properties"]
                country = (props.get("addr:country") or "ZZ").upper()
                oh = props.get("opening_hours", "").strip()
                if oh:
                    counter[country] += 1
    return counter


if __name__ == "__main__":
    print(count_pois_with_opening_hours(Path(sys.argv[1])))
