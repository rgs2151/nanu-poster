"""Detect directed motor movements in on-rail kymographs."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tifffile
from joblib import Parallel, delayed
from scipy import sparse
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import linear_sum_assignment
from scipy.signal import find_peaks
from scipy.sparse.csgraph import dijkstra
from skimage import measure, morphology


ROOT = Path(__file__).resolve().parents[2]
UNIT_DIR = Path(__file__).resolve().parent
ON_TO_OFF_PATH = ROOT / "data" / "on_to_off.tif"
OFF_TO_ON_PATH = ROOT / "data" / "off_to_on.tif"
SOURCE_CACHE_PATH = (
    ROOT / "parking" / "fluorescence_dynamics" / "cache" / "fluorescence_dynamics.npz"
)
CACHE_PATH = UNIT_DIR / "cache" / "motor_run.npz"
OUTPUT_PATH = UNIT_DIR / "plots" / "motor_run.pdf"

PARALLEL_WORKERS = os.cpu_count() or 1
MINIMUM_PATH_PIXELS = 12
PROFILE_RADIUS_PIXELS = 2
POSITION_SMOOTH_SIGMA = 0.8
POSITION_BACKGROUND_SIGMA = 4.0
PEAK_Z_THRESHOLD = 3.0
PEAK_PROMINENCE = 1.0
PEAK_MINIMUM_DISTANCE_PIXELS = 2
MAXIMUM_PEAKS_PER_FRAME = 12
MAXIMUM_STEP_PIXELS = 8.0
MAXIMUM_MISSED_FRAMES = 1
MINIMUM_TRACK_OBSERVATIONS = 6
MINIMUM_TRACK_DURATION_SECONDS = 6.0
MINIMUM_DISPLACEMENT_PIXELS = 3.0
MINIMUM_SPEED_PIXELS_PER_SECOND = 0.05
MAXIMUM_SPEED_PIXELS_PER_SECOND = 5.0
MINIMUM_LINEAR_R_SQUARED = 0.65
MINIMUM_DIRECTIONALITY = 0.65
BIN_WIDTH_MINUTES = 1.0
DISPLAY_WINDOW_MINUTES = 5.0

COLORS = {
    "off_to_on": "#991B1B",
    "on_to_off": "#166534",
}


@dataclass
class Track:
    frames: list[int]
    positions: list[float]
    strengths: list[float]


def setup_style():
    sns.set_theme(context="talk", style="ticks", palette="dark")
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["mathtext.fontset"] = "cm"
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["lines.linewidth"] = 1
    plt.rcParams["patch.linewidth"] = 0
    plt.rcParams["image.interpolation"] = "none"
    plt.rcParams["legend.frameon"] = False
    plt.rcParams["figure.dpi"] = 300
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["savefig.format"] = "pdf"
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["savefig.transparent"] = False


def array_sha256(array):
    contiguous = np.ascontiguousarray(array)
    return hashlib.sha256(contiguous.view(np.uint8)).hexdigest()


def load_motor_frame(tif, recording, index):
    if recording == "on_to_off":
        return tif.pages[index].asarray()[:, :256]
    return tif.pages[index * 2 + 1].asarray()


def longest_skeleton_path(component_mask):
    """Return the longest endpoint-to-endpoint path through a skeleton."""
    skeleton = morphology.skeletonize(component_mask)
    coordinates = np.argwhere(skeleton)
    if len(coordinates) < MINIMUM_PATH_PIXELS:
        return np.empty((0, 2), dtype=np.int32)

    lookup = {tuple(coordinate): index for index, coordinate in enumerate(coordinates)}
    rows = []
    columns = []
    weights = []
    for index, (row, column) in enumerate(coordinates):
        for row_delta, column_delta in ((0, 1), (1, -1), (1, 0), (1, 1)):
            neighbor = (int(row + row_delta), int(column + column_delta))
            neighbor_index = lookup.get(neighbor)
            if neighbor_index is None:
                continue
            weight = np.hypot(row_delta, column_delta)
            rows.extend((index, neighbor_index))
            columns.extend((neighbor_index, index))
            weights.extend((weight, weight))

    graph = sparse.csr_matrix(
        (weights, (rows, columns)),
        shape=(len(coordinates), len(coordinates)),
    )
    degree = np.diff(graph.indptr)
    candidates = np.flatnonzero(degree == 1)
    if not len(candidates):
        candidates = np.arange(len(coordinates))

    seed = int(candidates[0])
    distances = dijkstra(graph, indices=seed, directed=False)
    reachable = candidates[np.isfinite(distances[candidates])]
    if not len(reachable):
        return np.empty((0, 2), dtype=np.int32)
    start = int(reachable[np.argmax(distances[reachable])])

    distances, predecessors = dijkstra(
        graph,
        indices=start,
        directed=False,
        return_predecessors=True,
    )
    reachable = candidates[np.isfinite(distances[candidates])]
    stop = int(reachable[np.argmax(distances[reachable])])
    indices = [stop]
    while indices[-1] != start:
        predecessor = int(predecessors[indices[-1]])
        if predecessor < 0:
            return np.empty((0, 2), dtype=np.int32)
        indices.append(predecessor)
    indices.reverse()
    return coordinates[np.asarray(indices, dtype=int)].astype(np.int32)


def derive_paths(rail_mask):
    """Use one longest, unbranched centreline per connected rail structure."""
    labels = measure.label(rail_mask, connectivity=2)
    paths = []
    component_ids = []
    for component_id in range(1, int(labels.max()) + 1):
        path = longest_skeleton_path(labels == component_id)
        if len(path) >= MINIMUM_PATH_PIXELS:
            paths.append(path)
            component_ids.append(component_id)
    order = np.argsort([-len(path) for path in paths])
    paths = [paths[index] for index in order]
    component_ids = [component_ids[index] for index in order]
    return labels, paths, component_ids


def make_profile_matrix(labels, paths, component_ids, image_shape):
    """Average a two-pixel-radius cross-section inside the accepted rail region."""
    disk = morphology.disk(PROFILE_RADIUS_PIXELS).astype(bool)
    disk_offsets = np.argwhere(disk) - PROFILE_RADIUS_PIXELS
    row_indices = []
    pixel_indices = []
    values = []
    flat_path_coordinates = []
    path_offsets = [0]

    profile_index = 0
    for path, component_id in zip(paths, component_ids):
        for row, column in path:
            pixels = []
            for row_delta, column_delta in disk_offsets:
                candidate_row = int(row + row_delta)
                candidate_column = int(column + column_delta)
                if not (
                    0 <= candidate_row < image_shape[0]
                    and 0 <= candidate_column < image_shape[1]
                ):
                    continue
                if labels[candidate_row, candidate_column] == component_id:
                    pixels.append(candidate_row * image_shape[1] + candidate_column)
            if not pixels:
                pixels = [int(row) * image_shape[1] + int(column)]
            weight = 1.0 / len(pixels)
            row_indices.extend([profile_index] * len(pixels))
            pixel_indices.extend(pixels)
            values.extend([weight] * len(pixels))
            flat_path_coordinates.append((row, column))
            profile_index += 1
        path_offsets.append(profile_index)

    matrix = sparse.csr_matrix(
        (values, (row_indices, pixel_indices)),
        shape=(profile_index, int(np.prod(image_shape))),
        dtype=np.float32,
    )
    return (
        matrix,
        np.asarray(flat_path_coordinates, dtype=np.int32),
        np.asarray(path_offsets, dtype=np.int32),
        np.asarray(component_ids, dtype=np.int32),
    )


def project_frame_chunk(recording, start, stop, profile_matrix):
    data_path = ON_TO_OFF_PATH if recording == "on_to_off" else OFF_TO_ON_PATH
    with tifffile.TiffFile(data_path) as tif:
        frames = np.stack(
            [load_motor_frame(tif, recording, index) for index in range(start, stop)]
        )
    profiles = (profile_matrix @ frames.reshape(len(frames), -1).T).T
    return start, np.asarray(profiles, dtype=np.float32)


def build_raw_kymograph(recording, frame_count, profile_matrix):
    edges = np.linspace(0, frame_count, PARALLEL_WORKERS + 1, dtype=int)
    chunks = Parallel(
        n_jobs=PARALLEL_WORKERS,
        prefer="threads",
        require="sharedmem",
    )(
        delayed(project_frame_chunk)(
            recording,
            int(start),
            int(stop),
            profile_matrix,
        )
        for start, stop in zip(edges[:-1], edges[1:])
        if stop > start
    )
    chunks.sort(key=lambda item: item[0])
    return np.concatenate([item[1] for item in chunks], axis=0)


def preprocess_kymograph(raw_kymograph):
    position_smoothed = gaussian_filter1d(
        raw_kymograph,
        sigma=POSITION_SMOOTH_SIGMA,
        axis=1,
        mode="nearest",
    )
    broad_background = gaussian_filter1d(
        position_smoothed,
        sigma=POSITION_BACKGROUND_SIGMA,
        axis=1,
        mode="nearest",
    )
    residual = position_smoothed - broad_background
    median = np.median(residual, axis=1, keepdims=True)
    mad = np.median(np.abs(residual - median), axis=1, keepdims=True)
    scale = np.maximum(1.4826 * mad, 1.0)
    return np.clip((residual - median) / scale, -8.0, 20.0).astype(np.float32)


def peaks_for_frame(profile):
    peak_indices, properties = find_peaks(
        profile,
        height=PEAK_Z_THRESHOLD,
        prominence=PEAK_PROMINENCE,
        distance=PEAK_MINIMUM_DISTANCE_PIXELS,
    )
    strengths = properties["peak_heights"]
    if len(peak_indices) > MAXIMUM_PEAKS_PER_FRAME:
        keep = np.argsort(strengths)[-MAXIMUM_PEAKS_PER_FRAME:]
        peak_indices = peak_indices[keep]
        strengths = strengths[keep]
    order = np.argsort(peak_indices)
    return peak_indices[order].astype(float), strengths[order].astype(float)


def link_peaks(kymograph):
    """Link local peaks through time before classifying diagonal trajectories."""
    active = []
    completed = []
    for frame_index, profile in enumerate(kymograph):
        still_active = []
        for track in active:
            if frame_index - track.frames[-1] <= MAXIMUM_MISSED_FRAMES + 1:
                still_active.append(track)
            else:
                completed.append(track)
        active = still_active

        positions, strengths = peaks_for_frame(profile)
        if not len(positions):
            continue
        if not active:
            active = [
                Track([frame_index], [float(position)], [float(strength)])
                for position, strength in zip(positions, strengths)
            ]
            continue

        last_positions = np.asarray([track.positions[-1] for track in active])
        frame_gaps = np.asarray(
            [frame_index - track.frames[-1] for track in active],
            dtype=float,
        )
        cost = np.abs(last_positions[:, None] - positions[None, :])
        track_indices, peak_indices = linear_sum_assignment(cost)
        assigned_peaks = set()
        for track_index, peak_index in zip(track_indices, peak_indices):
            if cost[track_index, peak_index] > MAXIMUM_STEP_PIXELS * frame_gaps[track_index]:
                continue
            active[track_index].frames.append(frame_index)
            active[track_index].positions.append(float(positions[peak_index]))
            active[track_index].strengths.append(float(strengths[peak_index]))
            assigned_peaks.add(int(peak_index))
        for peak_index, (position, strength) in enumerate(zip(positions, strengths)):
            if peak_index not in assigned_peaks:
                active.append(
                    Track([frame_index], [float(position)], [float(strength)])
                )
    completed.extend(active)
    return completed


def classify_track(track, time_seconds):
    frames = np.asarray(track.frames, dtype=np.int32)
    positions = np.asarray(track.positions, dtype=float)
    elapsed = time_seconds[frames]
    duration = float(elapsed[-1] - elapsed[0]) if len(elapsed) > 1 else 0.0
    displacement = float(abs(positions[-1] - positions[0])) if len(positions) else 0.0
    path_travel = float(np.sum(np.abs(np.diff(positions))))
    directionality = displacement / path_travel if path_travel > 0 else 0.0

    if len(elapsed) > 1 and np.ptp(elapsed) > 0:
        slope, intercept = np.polyfit(elapsed, positions, 1)
        fitted = slope * elapsed + intercept
        total_sum_squares = float(np.sum((positions - positions.mean()) ** 2))
        residual_sum_squares = float(np.sum((positions - fitted) ** 2))
        r_squared = (
            1.0 - residual_sum_squares / total_sum_squares
            if total_sum_squares > 0
            else 0.0
        )
    else:
        slope = 0.0
        r_squared = 0.0

    accepted = (
        len(frames) >= MINIMUM_TRACK_OBSERVATIONS
        and duration >= MINIMUM_TRACK_DURATION_SECONDS
        and displacement >= MINIMUM_DISPLACEMENT_PIXELS
        and MINIMUM_SPEED_PIXELS_PER_SECOND <= abs(slope) <= MAXIMUM_SPEED_PIXELS_PER_SECOND
        and r_squared >= MINIMUM_LINEAR_R_SQUARED
        and directionality >= MINIMUM_DIRECTIONALITY
    )
    return {
        "accepted": accepted,
        "duration_seconds": duration,
        "displacement_pixels": displacement,
        "speed_pixels_per_second": float(slope),
        "r_squared": r_squared,
        "directionality": directionality,
        "mean_strength_z": float(np.mean(track.strengths)),
    }


def detect_tracks(processed_kymograph, path_offsets, time_seconds):
    """Detect tracks independently on each unbranched rail path."""
    all_tracks = []
    for path_index, (start, stop) in enumerate(
        zip(path_offsets[:-1], path_offsets[1:])
    ):
        path_kymograph = processed_kymograph[:, start:stop]
        for track in link_peaks(path_kymograph):
            summary = classify_track(track, time_seconds)
            all_tracks.append((path_index, track, summary))
    return all_tracks


def pack_tracks(tracks):
    point_offsets = [0]
    frames = []
    positions = []
    path_indices = []
    accepted = []
    duration = []
    displacement = []
    speed = []
    r_squared = []
    directionality = []
    mean_strength = []
    for path_index, track, summary in tracks:
        frames.extend(track.frames)
        positions.extend(track.positions)
        point_offsets.append(len(frames))
        path_indices.append(path_index)
        accepted.append(summary["accepted"])
        duration.append(summary["duration_seconds"])
        displacement.append(summary["displacement_pixels"])
        speed.append(summary["speed_pixels_per_second"])
        r_squared.append(summary["r_squared"])
        directionality.append(summary["directionality"])
        mean_strength.append(summary["mean_strength_z"])
    return {
        "track_point_offsets": np.asarray(point_offsets, dtype=np.int64),
        "track_frames": np.asarray(frames, dtype=np.int32),
        "track_positions": np.asarray(positions, dtype=np.float32),
        "track_path_index": np.asarray(path_indices, dtype=np.int32),
        "track_accepted": np.asarray(accepted, dtype=bool),
        "track_duration_seconds": np.asarray(duration, dtype=np.float32),
        "track_displacement_pixels": np.asarray(displacement, dtype=np.float32),
        "track_speed_pixels_per_second": np.asarray(speed, dtype=np.float32),
        "track_r_squared": np.asarray(r_squared, dtype=np.float32),
        "track_directionality": np.asarray(directionality, dtype=np.float32),
        "track_mean_strength_z": np.asarray(mean_strength, dtype=np.float32),
    }


def event_rate(time_min, packed_tracks):
    accepted = packed_tracks["track_accepted"]
    offsets = packed_tracks["track_point_offsets"]
    frames = packed_tracks["track_frames"]
    start_times = np.asarray(
        [time_min[frames[offsets[index]]] for index in np.flatnonzero(accepted)],
        dtype=float,
    )
    end_time = float(time_min[-1])
    edges = np.arange(0.0, np.floor(end_time) + 1.0, BIN_WIDTH_MINUTES)
    if len(edges) == 0 or edges[0] != 0:
        edges = np.asarray([0.0])
    if edges[-1] < end_time:
        edges = np.append(edges, end_time)
    counts, _ = np.histogram(start_times, bins=edges)
    widths = np.diff(edges)
    rate = counts / widths
    centers = edges[:-1] + widths / 2.0
    return start_times, edges, centers, counts, rate


def centered_rolling_mean(time_min, values, window_minutes):
    half_window = window_minutes / 2.0
    left = np.searchsorted(time_min, time_min - half_window, side="left")
    right = np.searchsorted(time_min, time_min + half_window, side="right")
    cumulative = np.pad(np.cumsum(values, dtype=float), (1, 0))
    return (cumulative[right] - cumulative[left]) / (right - left)


def build_recording_result(recording, source_cache):
    time_min = source_cache[f"{recording}_time_min"].astype(float)
    rail_mask = source_cache[f"{recording}_rail_mask"].astype(bool)
    labels, paths, component_ids = derive_paths(rail_mask)
    profile_matrix, path_coordinates, path_offsets, component_ids = (
        make_profile_matrix(labels, paths, component_ids, rail_mask.shape)
    )
    raw_kymograph = build_raw_kymograph(
        recording,
        len(time_min),
        profile_matrix,
    )
    processed_kymograph = preprocess_kymograph(raw_kymograph)
    tracks = detect_tracks(processed_kymograph, path_offsets, time_min * 60.0)
    packed_tracks = pack_tracks(tracks)
    start_times, bin_edges, bin_centers, event_counts, event_rate_values = event_rate(
        time_min,
        packed_tracks,
    )
    smoothed = centered_rolling_mean(
        bin_centers,
        event_rate_values,
        DISPLAY_WINDOW_MINUTES,
    )
    result = {
        "time_min": time_min,
        "rail_mask": rail_mask,
        "rail_mask_sha256": np.asarray(array_sha256(rail_mask)),
        "path_coordinates": path_coordinates,
        "path_offsets": path_offsets,
        "path_component_ids": component_ids,
        "raw_kymograph": raw_kymograph,
        "processed_kymograph": processed_kymograph,
        "accepted_start_time_min": start_times,
        "bin_edges_min": bin_edges,
        "bin_centers_min": bin_centers,
        "event_count": event_counts,
        "event_rate_per_minute": event_rate_values,
        "event_rate_smoothed": smoothed,
    }
    result.update(packed_tracks)
    return result


def build_cache():
    source_cache_sha256 = hashlib.sha256(SOURCE_CACHE_PATH.read_bytes()).hexdigest()
    results = {}
    with np.load(SOURCE_CACHE_PATH) as source_cache:
        for recording in ("off_to_on", "on_to_off"):
            recording_result = build_recording_result(recording, source_cache)
            results.update(
                {
                    f"{recording}_{name}": value
                    for name, value in recording_result.items()
                }
            )

    results.update(
        {
            "source_cache_sha256": np.asarray(source_cache_sha256),
            "parallel_workers": np.asarray(PARALLEL_WORKERS),
            "minimum_path_pixels": np.asarray(MINIMUM_PATH_PIXELS),
            "profile_radius_pixels": np.asarray(PROFILE_RADIUS_PIXELS),
            "position_smooth_sigma": np.asarray(POSITION_SMOOTH_SIGMA),
            "position_background_sigma": np.asarray(POSITION_BACKGROUND_SIGMA),
            "peak_z_threshold": np.asarray(PEAK_Z_THRESHOLD),
            "peak_prominence": np.asarray(PEAK_PROMINENCE),
            "maximum_step_pixels": np.asarray(MAXIMUM_STEP_PIXELS),
            "maximum_missed_frames": np.asarray(MAXIMUM_MISSED_FRAMES),
            "minimum_track_observations": np.asarray(MINIMUM_TRACK_OBSERVATIONS),
            "minimum_track_duration_seconds": np.asarray(
                MINIMUM_TRACK_DURATION_SECONDS
            ),
            "minimum_displacement_pixels": np.asarray(MINIMUM_DISPLACEMENT_PIXELS),
            "minimum_speed_pixels_per_second": np.asarray(
                MINIMUM_SPEED_PIXELS_PER_SECOND
            ),
            "maximum_speed_pixels_per_second": np.asarray(
                MAXIMUM_SPEED_PIXELS_PER_SECOND
            ),
            "minimum_linear_r_squared": np.asarray(MINIMUM_LINEAR_R_SQUARED),
            "minimum_directionality": np.asarray(MINIMUM_DIRECTIONALITY),
            "bin_width_minutes": np.asarray(BIN_WIDTH_MINUTES),
            "display_window_minutes": np.asarray(DISPLAY_WINDOW_MINUTES),
        }
    )
    np.savez_compressed(CACHE_PATH, **results)


def plot_motor_run(cache):
    setup_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.5), sharey=True)
    panels = [
        ("off_to_on", "OFF-to-ON"),
        ("on_to_off", "ON-to-OFF"),
    ]
    maximum = max(
        float(np.max(cache[f"{recording}_event_rate_smoothed"]))
        for recording, _ in panels
    )
    upper = max(1.0, np.ceil(maximum * 1.12))

    for ax, (recording, title) in zip(axes, panels):
        time_min = cache[f"{recording}_bin_centers_min"]
        smoothed = cache[f"{recording}_event_rate_smoothed"]
        ax.plot(
            time_min,
            smoothed,
            color=COLORS[recording],
            linewidth=1.4,
            label="5-minute average",
        )
        xmax = float(cache[f"{recording}_time_min"][-1])
        ax.set_xlim(0, xmax)
        ax.set_xticks([0, xmax])
        ax.set_ylim(-0.05 * upper, upper)
        ax.set_yticks([0, upper])
        ax.set_xlabel("Time (min)")
        ax.set_title(title)
        ax.legend(loc="upper left", fontsize=8, frameon=False)
        ax.set_box_aspect(1)
        sns.despine(ax=ax, trim=True, offset=10)

    axes[0].set_ylabel("On-rail movements per minute")
    fig.subplots_adjust(wspace=0.32)
    fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)


if __name__ == "__main__":
    if not CACHE_PATH.exists():
        build_cache()
    with np.load(CACHE_PATH) as cache:
        plot_motor_run(cache)
