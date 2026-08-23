"""Show the rail paths and accepted kymograph streaks used by motor_run.py."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

from motor_run import (
    CACHE_PATH,
    COLORS,
    SOURCE_CACHE_PATH,
    build_cache,
    setup_style,
)


UNIT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = UNIT_DIR / "plots" / "motor_run_diagnostic.pdf"
WINDOW_MINUTES = 1.0


def path_slices(cache, recording):
    offsets = cache[f"{recording}_path_offsets"]
    coordinates = cache[f"{recording}_path_coordinates"]
    return [
        coordinates[start:stop]
        for start, stop in zip(offsets[:-1], offsets[1:])
    ]


def selected_path_index(cache, recording):
    accepted = cache[f"{recording}_track_accepted"]
    path_indices = cache[f"{recording}_track_path_index"]
    path_count = len(cache[f"{recording}_path_offsets"]) - 1
    counts = np.bincount(path_indices[accepted], minlength=path_count)
    return int(np.argmax(counts))


def accepted_start_times(cache, recording, path_index):
    accepted = cache[f"{recording}_track_accepted"]
    path_indices = cache[f"{recording}_track_path_index"]
    offsets = cache[f"{recording}_track_point_offsets"]
    frames = cache[f"{recording}_track_frames"]
    time_min = cache[f"{recording}_time_min"]
    return np.asarray(
        [
            time_min[frames[offsets[track_index]]]
            for track_index in np.flatnonzero(
                accepted & (path_indices == path_index)
            )
        ],
        dtype=float,
    )


def diagnostic_windows(cache, recording, path_index):
    """Choose one quiet endpoint and the densest accepted-event window."""
    end_time = float(cache[f"{recording}_time_min"][-1])
    starts = accepted_start_times(cache, recording, path_index)
    if len(starts):
        candidates = np.clip(starts - 0.5, 0.0, end_time - WINDOW_MINUTES)
        counts = np.asarray(
            [
                np.count_nonzero(
                    (starts >= candidate)
                    & (starts < candidate + WINDOW_MINUTES)
                )
                for candidate in candidates
            ]
        )
        moving_start = float(candidates[np.argmax(counts)])
    else:
        moving_start = max(0.0, end_time / 2.0 - WINDOW_MINUTES / 2.0)

    endpoint_candidates = np.asarray([0.0, max(0.0, end_time - WINDOW_MINUTES)])
    endpoint_counts = np.asarray(
        [
            np.count_nonzero(
                (starts >= candidate)
                & (starts < candidate + WINDOW_MINUTES)
            )
            for candidate in endpoint_candidates
        ]
    )
    quiet_start = float(endpoint_candidates[np.argmin(endpoint_counts)])
    return quiet_start, moving_start


def add_track_overlays(ax, cache, recording, path_index, frame_start, frame_stop):
    accepted = cache[f"{recording}_track_accepted"]
    path_indices = cache[f"{recording}_track_path_index"]
    offsets = cache[f"{recording}_track_point_offsets"]
    frames = cache[f"{recording}_track_frames"]
    positions = cache[f"{recording}_track_positions"]
    time_min = cache[f"{recording}_time_min"]
    line_count = 0
    for track_index in np.flatnonzero(accepted & (path_indices == path_index)):
        start = offsets[track_index]
        stop = offsets[track_index + 1]
        track_frames = frames[start:stop]
        keep = (track_frames >= frame_start) & (track_frames < frame_stop)
        if np.count_nonzero(keep) < 2:
            continue
        ax.plot(
            positions[start:stop][keep],
            time_min[track_frames[keep]],
            color=COLORS[recording],
            linewidth=1.1,
        )
        line_count += 1
    return line_count


def show_kymograph(ax, cache, recording, path_index, window_start, label):
    time_min = cache[f"{recording}_time_min"]
    path_offsets = cache[f"{recording}_path_offsets"]
    position_start = path_offsets[path_index]
    position_stop = path_offsets[path_index + 1]
    frame_start = int(np.searchsorted(time_min, window_start, side="left"))
    frame_stop = int(
        np.searchsorted(time_min, window_start + WINDOW_MINUTES, side="right")
    )
    frame_stop = min(frame_stop, len(time_min))
    kymograph = cache[f"{recording}_processed_kymograph"][
        frame_start:frame_stop,
        position_start:position_stop,
    ]
    times = time_min[frame_start:frame_stop]
    ax.imshow(
        kymograph,
        cmap="gray",
        vmin=-1.0,
        vmax=6.0,
        aspect="auto",
        origin="upper",
        extent=(0, kymograph.shape[1] - 1, float(times[-1]), float(times[0])),
        interpolation="none",
    )
    line_count = add_track_overlays(
        ax,
        cache,
        recording,
        path_index,
        frame_start,
        frame_stop,
    )
    movement_word = "movement" if line_count == 1 else "movements"
    ax.set_title(f"{label}\n{line_count} {movement_word}", fontsize=9)
    ax.set_xlabel("Position on rail (pixels)", fontsize=8)
    ax.set_ylabel("Time (min)", fontsize=8)
    ax.tick_params(labelsize=7)


def plot_diagnostic(source_cache, cache):
    setup_style()
    fig, axes = plt.subplots(2, 3, figsize=(9.0, 6.2))
    panels = [
        ("off_to_on", "OFF-to-ON"),
        ("on_to_off", "ON-to-OFF"),
    ]

    for row, (recording, title) in enumerate(panels):
        rail_reference = source_cache[f"{recording}_rail_reference"]
        rail_mask = cache[f"{recording}_rail_mask"].astype(bool)
        paths = path_slices(cache, recording)
        chosen = selected_path_index(cache, recording)
        limits = np.percentile(rail_reference, [1.0, 99.8])

        image_ax = axes[row, 0]
        image_ax.imshow(
            rail_reference,
            cmap="gray",
            vmin=limits[0],
            vmax=limits[1],
            interpolation="none",
        )
        image_ax.contour(
            rail_mask,
            levels=[0.5],
            colors=[COLORS[recording]],
            linewidths=0.45,
            alpha=0.55,
        )
        segments = [
            np.column_stack((path[:, 1], path[:, 0]))
            for index, path in enumerate(paths)
            if index != chosen
        ]
        image_ax.add_collection(
            LineCollection(segments, colors="white", linewidths=0.35, alpha=0.7)
        )
        chosen_path = paths[chosen]
        image_ax.plot(
            chosen_path[:, 1],
            chosen_path[:, 0],
            color="black",
            linewidth=1.1,
        )
        accepted_count = int(
            np.count_nonzero(
                cache[f"{recording}_track_accepted"]
                & (cache[f"{recording}_track_path_index"] == chosen)
            )
        )
        image_ax.set_title(f"{title}\nselected rail: {accepted_count} movements", fontsize=9)
        image_ax.set_axis_off()

        quiet_start, moving_start = diagnostic_windows(
            cache,
            recording,
            chosen,
        )
        show_kymograph(
            axes[row, 1],
            cache,
            recording,
            chosen,
            quiet_start,
            "Stationary example",
        )
        show_kymograph(
            axes[row, 2],
            cache,
            recording,
            chosen,
            moving_start,
            "Movement example",
        )

    fig.subplots_adjust(
        left=0.055,
        right=0.985,
        bottom=0.09,
        top=0.95,
        wspace=0.34,
        hspace=0.42,
    )
    fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)


if __name__ == "__main__":
    if not CACHE_PATH.exists():
        build_cache()
    with np.load(SOURCE_CACHE_PATH) as source_cache, np.load(CACHE_PATH) as cache:
        plot_diagnostic(source_cache, cache)
