from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tifffile


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "on_to_off.tif"
OUTPUT_PATH = Path(__file__).resolve().parent / "plots" / "timing_consistency.pdf"

with tifffile.TiffFile(DATA_PATH) as tif:
    elapsed_ms = np.array(
        [page.tags["MicroManagerMetadata"].value["ElapsedTime-ms"] for page in tif.pages],
        dtype=float,
    )

actual_time_min = (elapsed_ms - elapsed_ms[0]) / 60_000
median_interval_ms = float(np.median(np.diff(elapsed_ms)))
constant_time_min = np.arange(elapsed_ms.size) * median_interval_ms / 60_000
final_difference_min = actual_time_min[-1] - constant_time_min[-1]
axis_max = float(max(actual_time_min[-1], constant_time_min[-1]))

sns.set_theme(context="talk", style="ticks", palette="dark")
plt.rcParams["font.family"] = "serif"
plt.rcParams["mathtext.fontset"] = "cm"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["lines.linewidth"] = 1
plt.rcParams["legend.frameon"] = False
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.facecolor"] = "white"
plt.rcParams["savefig.transparent"] = False

fig, ax = plt.subplots(figsize=(4.4, 4.4))
ax.plot(
    [0, axis_max],
    [0, axis_max],
    color="black",
    linestyle="--",
    label="Perfect constant timing",
)
ax.plot(
    constant_time_min,
    actual_time_min,
    color="darkred",
    label="Recorded timing",
)
ax.plot(
    constant_time_min[-1],
    actual_time_min[-1],
    marker="o",
    color="darkred",
    linestyle="None",
    markersize=5,
)
ax.annotate(
    f"{final_difference_min:+.2f} min",
    xy=(constant_time_min[-1], actual_time_min[-1]),
    xytext=(-8, -10),
    textcoords="offset points",
    ha="right",
    va="top",
    fontsize=9,
)

ax.set(
    title="ON to OFF timing consistency",
    xlabel="Constant-rate time (min)",
    ylabel="Actual TIFF time (min)",
    xlim=(0, axis_max),
    ylim=(0, axis_max),
    xticks=[0, axis_max],
    yticks=[0, axis_max],
)
ax.title.set_fontsize(12)
ax.xaxis.label.set_fontsize(11)
ax.yaxis.label.set_fontsize(11)
ax.tick_params(labelsize=10)
ax.set_aspect("equal", adjustable="box")
ax.legend(loc="upper left", fontsize=8)
sns.despine(ax=ax, trim=True, offset=10)

fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
plt.close(fig)
