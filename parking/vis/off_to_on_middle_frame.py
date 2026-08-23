from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tifffile


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "off_to_on.tif"
OUTPUT_PATH = Path(__file__).resolve().parent / "plots" / "off_to_on.pdf"

with tifffile.TiffFile(DATA_PATH) as tif:
    series = tif.series[0]
    if series.axes != "ZCYX" or series.shape[1] != 2:
        raise ValueError(f"Expected a two-channel ZCYX stack, found {series.axes} {series.shape}")

    timepoint_index = series.shape[0] // 2
    rail_view = tif.pages[timepoint_index * 2].asarray()
    motor_view = tif.pages[timepoint_index * 2 + 1].asarray()

plt.rcParams["font.family"] = "serif"
plt.rcParams["mathtext.fontset"] = "cm"
plt.rcParams["image.interpolation"] = "none"
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.facecolor"] = "white"
plt.rcParams["savefig.transparent"] = False

fig, axes = plt.subplots(1, 2, figsize=(6.2, 4.0))
for ax, image, title in zip(
    axes,
    [motor_view, rail_view],
    ["Motor proteins", "DNA rails"],
):
    display_min, display_max = np.percentile(image, [1.0, 99.8])
    ax.imshow(
        image,
        cmap="gray",
        vmin=display_min,
        vmax=display_max,
        interpolation="none",
    )
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()

fig.suptitle(f"OFF to ON: middle timepoint {timepoint_index}", fontsize=12, y=0.99)
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.83, wspace=0.08)
fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
plt.close(fig)
