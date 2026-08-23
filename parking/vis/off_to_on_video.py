from pathlib import Path

import numpy as np
import tifffile

from nanu_poster import write_dual_channel_video


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "off_to_on.tif"
OUTPUT_PATH = Path(__file__).resolve().parent / "plots" / "off_to_on.mp4"
OUTPUT_FRAMES = 240
OUTPUT_FPS = 12
ASSUMED_INTERVAL_SECONDS = 2.188

with tifffile.TiffFile(DATA_PATH) as tif:
    series = tif.series[0]
    if series.axes != "ZCYX" or series.shape[1] != 2:
        raise ValueError(
            f"Expected a two-channel ZCYX stack, found {series.axes} {series.shape}"
        )

    source_indices = np.linspace(0, series.shape[0] - 1, OUTPUT_FRAMES, dtype=int)
    rail_frames = np.stack([tif.pages[index * 2].asarray() for index in source_indices])
    motor_frames = np.stack(
        [tif.pages[index * 2 + 1].asarray() for index in source_indices]
    )

elapsed_minutes = source_indices * ASSUMED_INTERVAL_SECONDS / 60

write_dual_channel_video(
    motor_frames,
    rail_frames,
    elapsed_minutes,
    "OFF to ON",
    OUTPUT_PATH,
    OUTPUT_FPS,
)
