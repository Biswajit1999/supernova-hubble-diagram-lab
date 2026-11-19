"""Render the bundled Pantheon+ distance moduli and diagonal uncertainties."""

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / "data/reference.json").read_text(encoding="utf-8"))
points = source["points"]
included = [row for row in points if row["x"] >= 0.01]
excluded = [row for row in points if row["x"] < 0.01]

with plt.rc_context({"svg.fonttype": "none", "svg.hashsalt": "pantheon-subset", "font.size": 12}):
    figure, axis = plt.subplots(figsize=(8.4, 4.7), layout="constrained")
    axis.set_title("Pantheon+SH0ES distance–redshift measurements", loc="left", fontweight="bold")
    for rows, colour, label in (
        (excluded, "#777d82", f"Below the browser’s default redshift cut ({len(excluded)})"),
        (included, "#1e5269", f"At or above the cut ({len(included)})"),
    ):
        axis.errorbar(
            [row["x"] for row in rows], [row["y"] for row in rows],
            yerr=[row["y_err"] for row in rows], fmt="o", ms=2.5,
            color=colour, ecolor=colour, elinewidth=0.65, alpha=0.72, label=label,
        )
    axis.axvline(0.01, ls="--", color="#a94828", lw=1)
    axis.set(xscale="log", xlabel="Hubble-diagram redshift (zHD)", ylabel="Distance modulus (mag)")
    axis.grid(True, which="major", alpha=0.2)
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(loc="lower right", frameon=False, fontsize=9)
    figure.savefig(ROOT / "assets/pantheon-subset.svg", metadata={"Date": None})
    plt.close(figure)
