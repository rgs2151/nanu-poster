from pathlib import Path

import numpy as np
import tifffile

from nanu_poster import write_dual_channel_video


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "on_to_off.tif"
OUTPUT_PATH = Path(__file__).resolve().parent / "plots" / "on_to_off.mp4"
OUTPUT_FRAMES = 240
OUTPUT_FPS = 12

with tifffile.TiffFile(DATA_PATH) as tif:
    source_indices = np.linspace(0, len(tif.pages) - 1, OUTPUT_FRAMES, dtype=int)
    frames = np.stack([tif.pages[index].asarray() for index in source_indices])
    elapsed_ms = np.array(
        [
            tif.pages[index].tags["MicroManagerMetadata"].value["ElapsedTime-ms"]
            for index in source_indices
        ],
        dtype=float,
    )

split_column = frames.shape[2] // 2
motor_frames = frames[:, :, :split_column]
rail_frames = frames[:, :, split_column:]
elapsed_minutes = (elapsed_ms - elapsed_ms[0]) / 60_000

write_dual_channel_video(
    motor_frames,
    rail_frames,
    elapsed_minutes,
    "ON to OFF",
    OUTPUT_PATH,
    OUTPUT_FPS,
)
