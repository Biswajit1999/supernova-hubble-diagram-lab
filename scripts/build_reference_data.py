#!/usr/bin/env python3
"""Rebuild the deterministic browser subset from the official Pantheon+ release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/"
    "Pantheon%2B_Data/4_DISTANCES_AND_COVAR/Pantheon%2BSH0ES.dat"
)
EXPECTED_SHA256 = "1cb0fc379ef066afdc2ffd1857681cc478024570d8a3eba284fb645775198cf8"


def fetch_source() -> bytes:
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "supernova-hubble-diagram-lab/2"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def parse_rows(payload: bytes) -> list[dict[str, str]]:
    text = payload.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text), delimiter=" ", skipinitialspace=True)
    rows = [row for row in reader if row.get("CID")]
    rows.sort(key=lambda row: float(row["zHD"]))
    return rows


def stratified_indices(row_count: int, sample_count: int) -> list[int]:
    if sample_count < 2 or sample_count > row_count:
        raise ValueError("sample_count must be between 2 and row_count")
    return [math.floor(i * (row_count - 1) / (sample_count - 1)) for i in range(sample_count)]


def build_document(rows: list[dict[str, str]], sample_count: int) -> dict:
    points = []
    for index in stratified_indices(len(rows), sample_count):
        row = rows[index]
        points.append(
            {
                "x": round(float(row["zHD"]), 5),
                "y": round(float(row["MU_SH0ES"]), 4),
                "y_err": round(float(row["MU_SH0ES_ERR_DIAG"]), 4),
                "label": row["CID"],
            }
        )
    return {
        "dataset": "Pantheon+SH0ES Type Ia supernova compilation (stratified subsample)",
        "source": "Scolnic et al. 2022 / Brout et al. 2022 Pantheon+SH0ES data release",
        "source_url": "https://github.com/PantheonPlusSH0ES/DataRelease",
        "source_file": "Pantheon+_Data/4_DISTANCES_AND_COVAR/Pantheon+SH0ES.dat",
        "source_file_sha256": EXPECTED_SHA256,
        "citation": (
            "Scolnic, D. et al., 2022. The Pantheon+ Analysis: The Full Data Set and Light-curve "
            "Release. ApJ, 938, 113. Brout, D. et al., 2022. The Pantheon+ Analysis: "
            "Cosmological Constraints. ApJ, 938, 110."
        ),
        "n_full_sample": len(rows),
        "n_distinct_supernovae": 1550,
        "n_points": len(points),
        "selection": (
            f"Sort all {len(rows)} source rows by zHD and select "
            f"floor(i * ({len(rows)} - 1) / ({sample_count} - 1)) for i = 0..{sample_count - 1}."
        ),
        "columns": {"x": "zHD", "y": "MU_SH0ES", "y_err": "MU_SH0ES_ERR_DIAG", "label": "CID"},
        "analysis_scope": (
            "Visualization and diagonal-error teaching likelihood only. "
            "The official covariance products are not bundled or used."
        ),
        "x_label": "Redshift z (Hubble-diagram frame, zHD)",
        "y_label": "Distance modulus mu (MU_SH0ES)",
        "points": points,
        "requiredCitations": [
            (
                "Riess, A.G. et al., 1998. Observational evidence from supernovae for an "
                "accelerating universe and a cosmological constant. The Astronomical Journal, "
                "116(3), pp.1009-1038."
            ),
            (
                "Scolnic, D. et al., 2022. The Pantheon+ Analysis: The Full Data Set and "
                "Light-curve Release. ApJ, 938, 113."
            ),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/reference.json"))
    parser.add_argument("--count", type=int, default=180)
    args = parser.parse_args()

    payload = fetch_source()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(
            f"Upstream checksum changed: expected {EXPECTED_SHA256}, received {digest}. "
            "Review the release before updating the pinned hash."
        )
    document = build_document(parse_rows(payload), args.count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(document['points'])} points to {args.output} from SHA-256 {digest}")


if __name__ == "__main__":
    main()
