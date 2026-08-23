"""Export five consistently colored ON-to-OFF composite frames."""

from pathlib import Path
import os

import matplotlib.pyplot as plt
import numpy as np
import tifffile
from joblib import Parallel, delayed
from scipy.ndimage import gaussian_filter


ROOT = Path(__file__).resolve().parents[2]
UNIT_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "on_to_off.tif"
CACHE_PATH = UNIT_DIR / "cache" / "on_to_off_panels.npz"
OUTPUT_DIR = UNIT_DIR / "plots" / "on_off_panels"

PANEL_COUNT = 5
TEMPORAL_WINDOW_FRAMES = 5
SPATIAL_SMOOTH_SIGMA_PIXELS = 0.65
ROBUST_MAD_SCALE = 1.4826
BACKGROUND_STANDARD_DEVIATIONS = 3.0
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
    half_window = TEMPORAL_WINDOW_FRAMES // 2
    window_indices = []
    for frame_index in frame_indices:
        start = min(
            max(int(frame_index) - half_window, 0),
            frame_count - TEMPORAL_WINDOW_FRAMES,
        )
        window_indices.append(
            np.arange(start, start + TEMPORAL_WINDOW_FRAMES, dtype=int)
        )
    window_indices = np.asarray(window_indices)
    source_indices = np.unique(window_indices)
    source_frames = read_frames(source_indices).astype(np.float32)
    source_lookup = {
        int(frame_index): position
        for position, frame_index in enumerate(source_indices)
    }
    averaged_frames = np.stack(
        [
            source_frames[
                [source_lookup[int(frame_index)] for frame_index in window]
            ].mean(axis=0)
            for window in window_indices
        ]
    )

    split_column = averaged_frames.shape[2] // 2
    motor_frames = gaussian_filter(
        averaged_frames[:, :, :split_column],
        sigma=(0, SPATIAL_SMOOTH_SIGMA_PIXELS, SPATIAL_SMOOTH_SIGMA_PIXELS),
        mode="nearest",
    )
    rail_frames = gaussian_filter(
        averaged_frames[:, :, split_column:],
        sigma=(0, SPATIAL_SMOOTH_SIGMA_PIXELS, SPATIAL_SMOOTH_SIGMA_PIXELS),
        mode="nearest",
    )

    motor_median = float(np.median(motor_frames))
    motor_mad = float(np.median(np.abs(motor_frames - motor_median)))
    motor_black = (
        motor_median
        + BACKGROUND_STANDARD_DEVIATIONS * ROBUST_MAD_SCALE * motor_mad
    )
    motor_limits = np.asarray(
        [motor_black, np.percentile(motor_frames, HIGH_PERCENTILE)]
    )

    rail_median = np.median(rail_frames, axis=(1, 2))
    rail_mad = np.median(
        np.abs(rail_frames - rail_median[:, None, None]),
        axis=(1, 2),
    )
    rail_black = (
        rail_median
        + BACKGROUND_STANDARD_DEVIATIONS * ROBUST_MAD_SCALE * rail_mad
    )
    rail_white = np.percentile(
        rail_frames,
        HIGH_PERCENTILE,
        axis=(1, 2),
    )
    rail_limits = np.column_stack((rail_black, rail_white))

    np.savez_compressed(
        CACHE_PATH,
        frame_indices=frame_indices,
        window_indices=window_indices,
        motor_frames=motor_frames,
        rail_frames=rail_frames,
        motor_limits=motor_limits,
        rail_limits=rail_limits,
        high_percentile=np.asarray(HIGH_PERCENTILE),
        temporal_window_frames=np.asarray(TEMPORAL_WINDOW_FRAMES),
        spatial_smooth_sigma_pixels=np.asarray(SPATIAL_SMOOTH_SIGMA_PIXELS),
        robust_mad_scale=np.asarray(ROBUST_MAD_SCALE),
        background_standard_deviations=np.asarray(
            BACKGROUND_STANDARD_DEVIATIONS
        ),
        parallel_workers=np.asarray(PARALLEL_WORKERS),
    )


def normalize_channel(image, limits):
    normalized = (image.astype(np.float32) - float(limits[0])) / (
        float(limits[1]) - float(limits[0])
    )
    return np.clip(normalized, 0.0, 1.0)


def compose_frame(motor_frame, rail_frame, motor_limits, rail_limits):
    motor = normalize_channel(motor_frame, motor_limits)
    rail = normalize_channel(rail_frame, rail_limits)
    return np.clip(
        motor[:, :, None] * MOTOR_YELLOW
        + rail[:, :, None] * RAIL_BLUE,
        0.0,
        1.0,
    )


def export_panels(cache):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for panel_number, (motor_frame, rail_frame, rail_limits) in enumerate(
        zip(
            cache["motor_frames"],
            cache["rail_frames"],
            cache["rail_limits"],
        ),
        start=1,
    ):
        composite = compose_frame(
            motor_frame,
            rail_frame,
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
