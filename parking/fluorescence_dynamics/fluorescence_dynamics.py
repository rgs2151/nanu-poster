from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tifffile
from skimage import filters, morphology


ROOT = Path(__file__).resolve().parents[2]
UNIT_DIR = Path(__file__).resolve().parent
ON_TO_OFF_PATH = ROOT / "data" / "on_to_off.tif"
OFF_TO_ON_PATH = ROOT / "data" / "off_to_on.tif"
CACHE_PATH = UNIT_DIR / "cache" / "fluorescence_dynamics.npz"
OUTPUT_PATH = UNIT_DIR / "plots" / "fluorescence_dynamics.pdf"

REFERENCE_TIMEPOINTS = 101
SMOOTHING_SIGMA = 1.0
BACKGROUND_SIGMA = 12.0
MINIMUM_OBJECT_SIZE = 12
MASK_EXPANSION_RADIUS = 2
OFF_RAIL_INNER_RADIUS = 4
OFF_RAIL_OUTER_RADIUS = 10
BASELINE_MINUTES = 5.0
OFF_TO_ON_FRAME_INTERVAL_SECONDS = 2.188
ROLLING_WINDOW_SECONDS = 30.0

COLORS = {
    "off_to_on_rail": "#991B1B",
    "off_to_on_off_rail": "#E8A6A6",
    "on_to_off_rail": "#166534",
    "on_to_off_off_rail": "#86C995",
}


def segment_rails(rail_stack):
    rail_reference = np.median(rail_stack.astype(np.float32), axis=0)
    denoised_reference = filters.gaussian(
        rail_reference,
        sigma=SMOOTHING_SIGMA,
        preserve_range=True,
    )
    broad_background = filters.gaussian(
        denoised_reference,
        sigma=BACKGROUND_SIGMA,
        preserve_range=True,
    )
    processed_reference = denoised_reference - broad_background

    threshold = filters.threshold_otsu(processed_reference)
    rail_core = processed_reference > threshold
    rail_core = morphology.remove_small_objects(
        rail_core,
        max_size=MINIMUM_OBJECT_SIZE - 1,
    )
    rail_core = morphology.closing(rail_core, morphology.disk(1))
    rail_core = morphology.remove_small_holes(
        rail_core,
        max_size=MINIMUM_OBJECT_SIZE - 1,
    )
    rail_mask = morphology.dilation(
        rail_core,
        morphology.disk(MASK_EXPANSION_RADIUS),
    )

    off_rail_inner = morphology.dilation(
        rail_mask,
        morphology.disk(OFF_RAIL_INNER_RADIUS),
    )
    off_rail_outer = morphology.dilation(
        rail_mask,
        morphology.disk(OFF_RAIL_OUTER_RADIUS),
    )
    off_rail_mask = off_rail_outer & ~off_rail_inner
    return {
        "rail_reference": rail_reference,
        "processed_reference": processed_reference,
        "threshold": np.asarray(threshold),
        "rail_core": rail_core,
        "rail_mask": rail_mask,
        "off_rail_mask": off_rail_mask,
    }


def measure_motor_frame(motor_frame, rail_mask, off_rail_mask):
    rail_values = motor_frame[rail_mask]
    off_rail_values = motor_frame[off_rail_mask]
    detector_maximum = np.iinfo(motor_frame.dtype).max
    return (
        float(np.mean(rail_values)),
        float(np.mean(off_rail_values)),
        float(np.mean(rail_values == detector_maximum)),
        float(np.mean(off_rail_values == detector_maximum)),
    )


def normalize_trace(time_min, intensity):
    baseline = time_min <= BASELINE_MINUTES
    f0 = float(np.mean(intensity[baseline]))
    if not np.isfinite(f0) or f0 <= 0:
        raise ValueError(f"F0 must be positive and finite, found {f0}")
    return intensity / f0, f0


def measure_on_to_off():
    with tifffile.TiffFile(ON_TO_OFF_PATH) as tif:
        reference_indices = np.linspace(
            0,
            len(tif.pages) - 1,
            REFERENCE_TIMEPOINTS,
            dtype=int,
        )
        rail_stack = np.stack(
            [tif.pages[index].asarray()[:, 256:] for index in reference_indices]
        )
        segmentation = segment_rails(rail_stack)

        time_min = np.empty(len(tif.pages), dtype=float)
        rail_mean = np.empty(len(tif.pages), dtype=float)
        off_rail_mean = np.empty(len(tif.pages), dtype=float)
        rail_saturation_fraction = np.empty(len(tif.pages), dtype=float)
        off_rail_saturation_fraction = np.empty(len(tif.pages), dtype=float)

        for index, page in enumerate(tif.pages):
            full_frame = page.asarray()
            motor_frame = full_frame[:, :256]
            metadata = page.tags["MicroManagerMetadata"].value
            time_min[index] = float(metadata["ElapsedTime-ms"])
            (
                rail_mean[index],
                off_rail_mean[index],
                rail_saturation_fraction[index],
                off_rail_saturation_fraction[index],
            ) = measure_motor_frame(
                motor_frame,
                segmentation["rail_mask"],
                segmentation["off_rail_mask"],
            )

    time_min = (time_min - time_min[0]) / 60_000.0
    rail_ff0, rail_f0 = normalize_trace(time_min, rail_mean)
    off_rail_ff0, off_rail_f0 = normalize_trace(time_min, off_rail_mean)
    return {
        **segmentation,
        "reference_indices": reference_indices,
        "time_min": time_min,
        "rail_mean": rail_mean,
        "off_rail_mean": off_rail_mean,
        "rail_ff0": rail_ff0,
        "off_rail_ff0": off_rail_ff0,
        "rail_f0": np.asarray(rail_f0),
        "off_rail_f0": np.asarray(off_rail_f0),
        "rail_saturation_fraction": rail_saturation_fraction,
        "off_rail_saturation_fraction": off_rail_saturation_fraction,
    }


def measure_off_to_on():
    with tifffile.TiffFile(OFF_TO_ON_PATH) as tif:
        series = tif.series[0]
        if series.axes != "ZCYX" or series.shape[1] != 2:
            raise ValueError(
                f"Expected a two-channel ZCYX stack, found {series.axes} {series.shape}"
            )

        timepoints = series.shape[0]
        reference_indices = np.linspace(
            0,
            timepoints - 1,
            REFERENCE_TIMEPOINTS,
            dtype=int,
        )
        rail_stack = np.stack(
            [tif.pages[index * 2].asarray() for index in reference_indices]
        )
        segmentation = segment_rails(rail_stack)

        rail_mean = np.empty(timepoints, dtype=float)
        off_rail_mean = np.empty(timepoints, dtype=float)
        rail_saturation_fraction = np.empty(timepoints, dtype=float)
        off_rail_saturation_fraction = np.empty(timepoints, dtype=float)

        for index in range(timepoints):
            motor_frame = tif.pages[index * 2 + 1].asarray()
            (
                rail_mean[index],
                off_rail_mean[index],
                rail_saturation_fraction[index],
                off_rail_saturation_fraction[index],
            ) = measure_motor_frame(
                motor_frame,
                segmentation["rail_mask"],
                segmentation["off_rail_mask"],
            )

    time_min = (
        np.arange(timepoints, dtype=float)
        * OFF_TO_ON_FRAME_INTERVAL_SECONDS
        / 60.0
    )
    rail_ff0, rail_f0 = normalize_trace(time_min, rail_mean)
    off_rail_ff0, off_rail_f0 = normalize_trace(time_min, off_rail_mean)
    return {
        **segmentation,
        "reference_indices": reference_indices,
        "time_min": time_min,
        "rail_mean": rail_mean,
        "off_rail_mean": off_rail_mean,
        "rail_ff0": rail_ff0,
        "off_rail_ff0": off_rail_ff0,
        "rail_f0": np.asarray(rail_f0),
        "off_rail_f0": np.asarray(off_rail_f0),
        "rail_saturation_fraction": rail_saturation_fraction,
        "off_rail_saturation_fraction": off_rail_saturation_fraction,
    }


def build_cache():
    datasets = {
        "on_to_off": measure_on_to_off(),
        "off_to_on": measure_off_to_on(),
    }
    cache = {
        f"{recording}_{name}": value
        for recording, dataset in datasets.items()
        for name, value in dataset.items()
    }
    cache.update(
        {
            "reference_timepoints": np.asarray(REFERENCE_TIMEPOINTS),
            "smoothing_sigma": np.asarray(SMOOTHING_SIGMA),
            "background_sigma": np.asarray(BACKGROUND_SIGMA),
            "minimum_object_size": np.asarray(MINIMUM_OBJECT_SIZE),
            "mask_expansion_radius": np.asarray(MASK_EXPANSION_RADIUS),
            "off_rail_inner_radius": np.asarray(OFF_RAIL_INNER_RADIUS),
            "off_rail_outer_radius": np.asarray(OFF_RAIL_OUTER_RADIUS),
            "baseline_minutes": np.asarray(BASELINE_MINUTES),
            "off_to_on_frame_interval_seconds": np.asarray(
                OFF_TO_ON_FRAME_INTERVAL_SECONDS
            ),
        }
    )
    np.savez_compressed(CACHE_PATH, **cache)


def setup_style():
    sns.set_theme(context="talk", style="ticks", palette="dark")
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["mathtext.fontset"] = "cm"
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["lines.linewidth"] = 1
    plt.rcParams["patch.linewidth"] = 0
    plt.rcParams["legend.frameon"] = False
    plt.rcParams["figure.dpi"] = 300
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["savefig.transparent"] = False


def centered_rolling_mean(time_min, values):
    half_window_min = ROLLING_WINDOW_SECONDS / 120.0
    left = np.searchsorted(time_min, time_min - half_window_min, side="left")
    right = np.searchsorted(time_min, time_min + half_window_min, side="right")
    cumulative = np.concatenate([[0.0], np.cumsum(values, dtype=float)])
    return (cumulative[right] - cumulative[left]) / (right - left)


def plot_fluorescence_dynamics(cache):
    setup_style()
    fig, ax = plt.subplots(figsize=(4.2, 3.5))

    lines = [
        (
            "off_to_on",
            "rail_ff0",
            "OFF-to-ON rail",
            COLORS["off_to_on_rail"],
        ),
        (
            "off_to_on",
            "off_rail_ff0",
            "OFF-to-ON off rail",
            COLORS["off_to_on_off_rail"],
        ),
        (
            "on_to_off",
            "rail_ff0",
            "ON-to-OFF rail",
            COLORS["on_to_off_rail"],
        ),
        (
            "on_to_off",
            "off_rail_ff0",
            "ON-to-OFF off rail",
            COLORS["on_to_off_off_rail"],
        ),
    ]
    plotted_values = []
    for recording, signal, label, color in lines:
        time_min = cache[f"{recording}_time_min"]
        values = centered_rolling_mean(
            time_min,
            cache[f"{recording}_{signal}"],
        )
        plotted_values.append(values)
        ax.plot(
            time_min,
            values,
            color=color,
            linestyle="-",
            label=label,
        )

    ax.set_xlabel("Time (min)")
    ax.set_ylabel(r"$F/F_0$")

    xmax = max(
        float(cache["on_to_off_time_min"][-1]),
        float(cache["off_to_on_time_min"][-1]),
    )
    ax.set_xlim(0, xmax)
    ax.set_xticks([0, xmax])

    all_values = np.concatenate(plotted_values)
    value_min = float(np.nanmin(all_values))
    value_max = float(np.nanmax(all_values))
    padding = 0.05 * (value_max - value_min)
    y_min = max(0.0, np.floor((value_min - padding) * 10.0) / 10.0)
    y_max = np.ceil((value_max + padding) * 10.0) / 10.0
    ax.set_ylim(y_min, y_max)
    ax.set_yticks([y_min, y_max])

    ax.legend(loc="best", fontsize=7, frameon=False)
    sns.despine(ax=ax, trim=True, offset=10)
    fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)


if not CACHE_PATH.exists():
    build_cache()

with np.load(CACHE_PATH) as cache:
    plot_fluorescence_dynamics(cache)
