from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tifffile


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "on_to_off.tif"
OUTPUT_PATH = Path(__file__).resolve().parent / "plots" / "on_to_off.pdf"

with tifffile.TiffFile(DATA_PATH) as tif:
    frame_index = len(tif.pages) // 2
    frame = tif.pages[frame_index].asarray()

split_column = frame.shape[1] // 2
motor_view = frame[:, :split_column]
rail_view = frame[:, split_column:]

plt.rcParams["font.family"] = "serif"
plt.rcParams["mathtext.fontset"] = "cm"
plt.rcParams["image.interpolation"] = "none"
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.facecolor"] = "white"
plt.rcParams["savefig.transparent"] = False

fig, axes = plt.subplots(1, 2, figsize=(5.2, 5.0))
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

fig.suptitle(f"ON to OFF: middle frame {frame_index}", fontsize=12, y=0.99)
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.85, wspace=0.08)
fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
plt.close(fig)
