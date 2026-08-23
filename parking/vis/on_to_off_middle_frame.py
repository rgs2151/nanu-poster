from pathlib import Path

import matplotlib.pyplot as plt
import tifffile

from nanu_poster import create_dual_channel_figure, display_limits


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "on_to_off.tif"
OUTPUT_PATH = Path(__file__).resolve().parent / "plots" / "on_to_off.pdf"

with tifffile.TiffFile(DATA_PATH) as tif:
    frame_index = len(tif.pages) // 2
    frame = tif.pages[frame_index].asarray()

split_column = frame.shape[1] // 2
motor_view = frame[:, :split_column]
rail_view = frame[:, split_column:]

fig, _, _ = create_dual_channel_figure(
    motor_view,
    rail_view,
    display_limits(motor_view),
    display_limits(rail_view),
    "ON to OFF",
)
fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
plt.close(fig)
