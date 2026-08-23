from pathlib import Path

import matplotlib.pyplot as plt
import tifffile

from nanu_poster import create_dual_channel_figure, display_limits


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

fig, _, _ = create_dual_channel_figure(
    motor_view,
    rail_view,
    display_limits(motor_view),
    display_limits(rail_view),
    "OFF to ON",
)
fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
plt.close(fig)
