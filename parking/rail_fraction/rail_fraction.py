import hashlib
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tifffile
from joblib import Parallel, delayed


ROOT = Path(__file__).resolve().parents[2]
UNIT_DIR = Path(__file__).resolve().parent
ON_TO_OFF_PATH = ROOT / "data" / "on_to_off.tif"
OFF_TO_ON_PATH = ROOT / "data" / "off_to_on.tif"
SOURCE_CACHE_PATH = (
    ROOT / "parking" / "fluorescence_dynamics" / "cache" / "fluorescence_dynamics.npz"
)
CACHE_PATH = UNIT_DIR / "cache" / "rail_fraction.npz"
OUTPUT_PATH = UNIT_DIR / "plots" / "rail_fraction.pdf"

BASELINE_MINUTES = 5.0
THRESHOLD_MAD_MULTIPLIER = 3.0
ROLLING_WINDOW_SECONDS = 30.0
PARALLEL_WORKERS = os.cpu_count() or 1

COLORS = {
    "off_to_on": "#991B1B",
    "on_to_off": "#166534",
}


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


def load_motor_frame(tif, recording, index):
    if recording == "on_to_off":
        return tif.pages[index].asarray()[:, :256]
    return tif.pages[index * 2 + 1].asarray()


def fixed_background_threshold(recording, time_min, off_rail_mask):
    data_path = ON_TO_OFF_PATH if recording == "on_to_off" else OFF_TO_ON_PATH
    baseline_indices = np.flatnonzero(time_min <= BASELINE_MINUTES)
    with tifffile.TiffFile(data_path) as tif:
        baseline_values = np.concatenate(
            [
                load_motor_frame(tif, recording, int(index))[off_rail_mask]
                for index in baseline_indices
            ]
        )

    baseline_median = float(np.median(baseline_values))
    baseline_mad = float(np.median(np.abs(baseline_values - baseline_median)))
    threshold = baseline_median + THRESHOLD_MAD_MULTIPLIER * baseline_mad

    histogram_min, histogram_percentile_max = np.percentile(
        baseline_values,
        [0.2, 99.8],
    )
    histogram_max = max(float(histogram_percentile_max), threshold * 1.05)
    histogram_edges = np.linspace(float(histogram_min), histogram_max, 81)
    histogram_density, _ = np.histogram(
        baseline_values,
        bins=histogram_edges,
        density=True,
    )
    return {
        "baseline_off_rail_median": np.asarray(baseline_median),
        "baseline_off_rail_mad": np.asarray(baseline_mad),
        "motor_positive_threshold": np.asarray(threshold),
        "baseline_histogram_edges": histogram_edges,
        "baseline_histogram_density": histogram_density,
        "baseline_frame_count": np.asarray(len(baseline_indices)),
    }


def measure_fraction_chunk(recording, start, stop, rail_mask, threshold):
    data_path = ON_TO_OFF_PATH if recording == "on_to_off" else OFF_TO_ON_PATH
    with tifffile.TiffFile(data_path) as tif:
        motor_frames = np.stack(
            [
                load_motor_frame(tif, recording, index)
                for index in range(start, stop)
            ]
        )
    positive_counts = np.count_nonzero(
        motor_frames[:, rail_mask] > threshold,
        axis=1,
    )
    return start, positive_counts


def measure_positive_fraction(recording, time_min, rail_mask, threshold):
    edges = np.linspace(
        0,
        len(time_min),
        PARALLEL_WORKERS + 1,
        dtype=int,
    )
    chunks = Parallel(
        n_jobs=PARALLEL_WORKERS,
        prefer="threads",
        require="sharedmem",
    )(
        delayed(measure_fraction_chunk)(
            recording,
            int(start),
            int(stop),
            rail_mask,
            threshold,
        )
        for start, stop in zip(edges[:-1], edges[1:])
        if stop > start
    )
    chunks.sort(key=lambda chunk: chunk[0])
    positive_count = np.concatenate([chunk[1] for chunk in chunks])
    rail_pixel_count = int(np.count_nonzero(rail_mask))
    fraction_percent = 100.0 * positive_count / rail_pixel_count
    return positive_count, rail_pixel_count, fraction_percent


def centered_rolling_mean(time_min, values):
    half_window_min = ROLLING_WINDOW_SECONDS / 120.0
    left = np.searchsorted(time_min, time_min - half_window_min, side="left")
    right = np.searchsorted(time_min, time_min + half_window_min, side="right")
    cumulative = np.pad(np.cumsum(values, dtype=float), (1, 0))
    return (cumulative[right] - cumulative[left]) / (right - left)


def array_sha256(array):
    contiguous = np.ascontiguousarray(array)
    return hashlib.sha256(contiguous.view(np.uint8)).hexdigest()


def build_cache():
    results = {}
    with np.load(SOURCE_CACHE_PATH) as source_cache:
        source_cache_sha256 = hashlib.sha256(SOURCE_CACHE_PATH.read_bytes()).hexdigest()
        for recording in ["off_to_on", "on_to_off"]:
            time_min = source_cache[f"{recording}_time_min"]
            rail_mask = source_cache[f"{recording}_rail_mask"].astype(bool)
            off_rail_mask = source_cache[f"{recording}_off_rail_mask"].astype(bool)
            threshold_result = fixed_background_threshold(
                recording,
                time_min,
                off_rail_mask,
            )
            threshold = float(threshold_result["motor_positive_threshold"])
            positive_count, rail_pixel_count, fraction_percent = (
                measure_positive_fraction(
                    recording,
                    time_min,
                    rail_mask,
                    threshold,
                )
            )
            results.update(
                {
                    f"{recording}_time_min": time_min,
                    f"{recording}_positive_count": positive_count,
                    f"{recording}_rail_pixel_count": np.asarray(rail_pixel_count),
                    f"{recording}_fraction_percent": fraction_percent,
                    f"{recording}_fraction_smoothed": centered_rolling_mean(
                        time_min,
                        fraction_percent,
                    ),
                    f"{recording}_rail_mask_sha256": np.asarray(
                        array_sha256(rail_mask)
                    ),
                    f"{recording}_off_rail_mask_sha256": np.asarray(
                        array_sha256(off_rail_mask)
                    ),
                }
            )
            results.update(
                {
                    f"{recording}_{name}": value
                    for name, value in threshold_result.items()
                }
            )

    results.update(
        {
            "source_cache_sha256": np.asarray(source_cache_sha256),
            "baseline_minutes": np.asarray(BASELINE_MINUTES),
            "threshold_mad_multiplier": np.asarray(
                THRESHOLD_MAD_MULTIPLIER
            ),
            "rolling_window_seconds": np.asarray(ROLLING_WINDOW_SECONDS),
            "parallel_workers": np.asarray(PARALLEL_WORKERS),
        }
    )
    np.savez_compressed(CACHE_PATH, **results)


def plot_rail_fraction(cache):
    setup_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.5), sharey=True)
    panels = [
        ("off_to_on", "OFF-to-ON"),
        ("on_to_off", "ON-to-OFF"),
    ]

    for ax, (recording, title) in zip(axes, panels):
        time_min = cache[f"{recording}_time_min"]
        fraction = cache[f"{recording}_fraction_percent"]
        smoothed = cache[f"{recording}_fraction_smoothed"]
        color = COLORS[recording]

        ax.plot(
            time_min,
            fraction,
            color=color,
            alpha=0.22,
            linewidth=0.6,
            label="Raw",
        )
        ax.plot(
            time_min,
            smoothed,
            color=color,
            linewidth=1.4,
            label="30 s mean",
        )
        xmax = float(time_min[-1])
        ax.set_xlim(0, xmax)
        ax.set_xticks([0, xmax])
        ax.set_ylim(-2.5, 52.5)
        ax.set_yticks([0, 50])
        ax.set_xlabel("Time (min)")
        ax.set_title(title)
        ax.legend(loc="upper left", fontsize=8, frameon=False)
        ax.set_box_aspect(1)
        sns.despine(ax=ax, trim=True, offset=10)

    axes[0].set_ylabel("Rail fraction (%)")
    fig.subplots_adjust(wspace=0.32)
    fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)


if __name__ == "__main__":
    if not CACHE_PATH.exists():
        build_cache()
    with np.load(CACHE_PATH) as cache:
        plot_rail_fraction(cache)
