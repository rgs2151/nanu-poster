"""Export five consistently colored ON-to-OFF composite frames."""

from pathlib import Path
import os

import matplotlib.pyplot as plt
import numpy as np
import tifffile
from joblib import Parallel, delayed


ROOT = Path(__file__).resolve().parents[2]
UNIT_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "on_to_off.tif"
CACHE_PATH = UNIT_DIR / "cache" / "on_to_off_panels.npz"
OUTPUT_DIR = UNIT_DIR / "plots" / "on_off_panels"

PANEL_COUNT = 5
CONTRAST_SURVEY_FRAMES = 240
LOW_PERCENTILE = 1.0
HIGH_PERCENTILE = 99.8
PARALLEL_WORKERS = os.cpu_count() or 1

# Standard ImageJ/Fiji monochrome channel LUT endpoints.
MOTOR_YELLOW = np.asarray([1.0, 1.0, 0.0], dtype=np.float32)
RAIL_BLUE = np.asarray([0.0, 0.0, 1.0], dtype=np.float32)


def read_frame_chunk(indices):
    with tifffile.TiffFile(DATA_PATH) as tif:
        return np.stack([tif.pages[int(index)].asarray() for index in indices])


def read_frames(indices):
    chunks = [
        chunk
        for chunk in np.array_split(indices, PARALLEL_WORKERS)
        if len(chunk)
    ]
    arrays = Parallel(
        n_jobs=PARALLEL_WORKERS,
        prefer="threads",
        require="sharedmem",
    )(delayed(read_frame_chunk)(chunk) for chunk in chunks)
    return np.concatenate(arrays, axis=0)


def build_cache():
    with tifffile.TiffFile(DATA_PATH) as tif:
        frame_count = len(tif.pages)

    frame_indices = np.linspace(0, frame_count - 1, PANEL_COUNT, dtype=int)
    survey_indices = np.linspace(
        0,
        frame_count - 1,
        CONTRAST_SURVEY_FRAMES,
        dtype=int,
    )
    survey_frames = read_frames(survey_indices)
    split_column = survey_frames.shape[2] // 2
    motor_limits = np.percentile(
        survey_frames[:, :, :split_column],
        [LOW_PERCENTILE, HIGH_PERCENTILE],
    )
    selected_frames = read_frames(frame_indices)
    rail_limits = np.percentile(
        selected_frames[:, :, split_column:],
        [LOW_PERCENTILE, HIGH_PERCENTILE],
        axis=(1, 2),
    ).T

    np.savez_compressed(
        CACHE_PATH,
        frame_indices=frame_indices,
        survey_indices=survey_indices,
        selected_frames=selected_frames,
        motor_limits=motor_limits,
        rail_limits=rail_limits,
        low_percentile=np.asarray(LOW_PERCENTILE),
        high_percentile=np.asarray(HIGH_PERCENTILE),
        parallel_workers=np.asarray(PARALLEL_WORKERS),
    )


def normalize_channel(image, limits):
    normalized = (image.astype(np.float32) - float(limits[0])) / (
        float(limits[1]) - float(limits[0])
    )
    return np.clip(normalized, 0.0, 1.0)


def compose_frame(frame, motor_limits, rail_limits):
    split_column = frame.shape[1] // 2
    motor = normalize_channel(frame[:, :split_column], motor_limits)
    rail = normalize_channel(frame[:, split_column:], rail_limits)
    return np.clip(
        motor[:, :, None] * MOTOR_YELLOW
        + rail[:, :, None] * RAIL_BLUE,
        0.0,
        1.0,
    )


def export_panels(cache):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame_indices = cache["frame_indices"]
    for panel_number, (frame_index, frame, rail_limits) in enumerate(
        zip(
            frame_indices,
            cache["selected_frames"],
            cache["rail_limits"],
        ),
        start=1,
    ):
        composite = compose_frame(
            frame,
            cache["motor_limits"],
            rail_limits,
        )
        output_path = OUTPUT_DIR / f"on_to_off_{panel_number:02d}.png"
        plt.imsave(output_path, composite)


if __name__ == "__main__":
    if not CACHE_PATH.exists():
        build_cache()
    with np.load(CACHE_PATH) as cache:
        export_panels(cache)
