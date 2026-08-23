import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tifffile
from joblib import Parallel, delayed
from scipy import sparse
from skimage import filters, measure, morphology, segmentation


ROOT = Path(__file__).resolve().parents[2]
UNIT_DIR = Path(__file__).resolve().parent
ON_TO_OFF_PATH = ROOT / "data" / "on_to_off.tif"
OFF_TO_ON_PATH = ROOT / "data" / "off_to_on.tif"
CACHE_PATH = UNIT_DIR / "cache" / "fluorescence_dynamics.npz"
COMPONENT_CACHE_PATH = UNIT_DIR / "cache" / "fluorescence_components.npz"
BOOTSTRAP_CACHE_PATH = UNIT_DIR / "cache" / "fluorescence_bootstrap.npz"
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
BOOTSTRAP_SAMPLES = 1_000
BOOTSTRAP_SEED = 2_151
CONFIDENCE_LEVEL = 0.95
CLUSTER_FORMING_Z = 1.96
TRIPLE_STAR_P = 0.001
PARALLEL_WORKERS = os.cpu_count() or 1

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


def component_geometry(rail_mask, off_rail_mask):
    rail_labels = measure.label(rail_mask, connectivity=2)
    off_rail_labels = segmentation.expand_labels(
        rail_labels,
        distance=OFF_RAIL_OUTER_RADIUS,
    )
    off_rail_labels = np.where(off_rail_mask, off_rail_labels, 0)

    components = int(rail_labels.max())
    rail_counts = np.bincount(
        rail_labels.ravel(),
        minlength=components + 1,
    )[1:]
    off_rail_counts = np.bincount(
        off_rail_labels.ravel(),
        minlength=components + 1,
    )[1:]
    if np.any(rail_counts == 0) or np.any(off_rail_counts == 0):
        raise ValueError("Every rail component must have rail and off-rail pixels")
    return rail_labels, off_rail_labels, rail_counts, off_rail_counts


def component_membership(labels, components):
    pixel_indices = np.flatnonzero(labels.ravel())
    component_indices = labels.ravel()[pixel_indices] - 1
    return sparse.csr_matrix(
        (
            np.ones(len(pixel_indices), dtype=float),
            (component_indices, pixel_indices),
        ),
        shape=(components, labels.size),
    )


def measure_component_chunk(
    recording,
    start,
    stop,
    combined_membership,
):
    data_path = ON_TO_OFF_PATH if recording == "on_to_off" else OFF_TO_ON_PATH
    with tifffile.TiffFile(data_path) as tif:
        if recording == "on_to_off":
            motor_frames = np.stack(
                [tif.pages[index].asarray()[:, :256] for index in range(start, stop)]
            )
        else:
            motor_frames = np.stack(
                [
                    tif.pages[index * 2 + 1].asarray()
                    for index in range(start, stop)
                ]
            )
    component_sums = (combined_membership @ motor_frames.reshape(stop - start, -1).T).T
    return start, component_sums


def measure_component_time_courses(recording, rail_labels, off_rail_labels):
    components = int(rail_labels.max())
    timepoints = 2_000 if recording == "on_to_off" else 2_089
    combined_membership = sparse.vstack(
        [
            component_membership(rail_labels, components),
            component_membership(off_rail_labels, components),
        ],
        format="csr",
    )
    edges = np.linspace(
        0,
        timepoints,
        PARALLEL_WORKERS + 1,
        dtype=int,
    )
    chunks = Parallel(
        n_jobs=PARALLEL_WORKERS,
        prefer="threads",
        require="sharedmem",
    )(
        delayed(measure_component_chunk)(
            recording,
            int(start),
            int(stop),
            combined_membership,
        )
        for start, stop in zip(edges[:-1], edges[1:])
        if stop > start
    )
    chunks.sort(key=lambda chunk: chunk[0])
    component_sums = np.concatenate([chunk[1] for chunk in chunks], axis=0)
    rail_sums = component_sums[:, :components]
    off_rail_sums = component_sums[:, components:]
    return rail_sums, off_rail_sums


def centered_rolling_mean_matrix(time_min, values):
    half_window_min = ROLLING_WINDOW_SECONDS / 120.0
    left = np.searchsorted(time_min, time_min - half_window_min, side="left")
    right = np.searchsorted(time_min, time_min + half_window_min, side="right")
    cumulative = np.pad(
        np.cumsum(values, axis=1, dtype=float),
        ((0, 0), (1, 0)),
    )
    return (cumulative[:, right] - cumulative[:, left]) / (right - left)


def cluster_mass_test(observed_difference, bootstrap_difference, difference_se):
    bootstrap_null = (
        bootstrap_difference - observed_difference[None, :]
    ) / difference_se[None, :]
    observed_standardized = observed_difference / difference_se

    bootstrap_max_cluster_mass = np.zeros(BOOTSTRAP_SAMPLES, dtype=float)
    for bootstrap_index, null_trace in enumerate(bootstrap_null):
        masses = [
            np.abs(null_trace[start : stop + 1]).sum()
            for start, stop in significant_runs(
                np.abs(null_trace) >= CLUSTER_FORMING_Z
            )
        ]
        bootstrap_max_cluster_mass[bootstrap_index] = max(masses, default=0.0)

    cluster_p = np.ones(len(observed_difference), dtype=float)
    cluster_starts = []
    cluster_stops = []
    cluster_p_values = []
    for start, stop in significant_runs(
        np.abs(observed_standardized) >= CLUSTER_FORMING_Z
    ):
        observed_mass = np.abs(observed_standardized[start : stop + 1]).sum()
        p_value = (
            1 + np.sum(bootstrap_max_cluster_mass >= observed_mass)
        ) / (BOOTSTRAP_SAMPLES + 1)
        cluster_p[start : stop + 1] = p_value
        cluster_starts.append(start)
        cluster_stops.append(stop)
        cluster_p_values.append(p_value)

    return {
        "observed_standardized_difference": observed_standardized,
        "bootstrap_max_cluster_mass": bootstrap_max_cluster_mass,
        "cluster_p": cluster_p,
        "cluster_start_index": np.asarray(cluster_starts, dtype=int),
        "cluster_stop_index": np.asarray(cluster_stops, dtype=int),
        "cluster_p_value": np.asarray(cluster_p_values, dtype=float),
        "triple_significant": cluster_p <= TRIPLE_STAR_P,
    }


def bootstrap_recording(
    time_min,
    observed_rail,
    observed_off_rail,
    rail_sums,
    off_rail_sums,
    rail_counts,
    off_rail_counts,
    rng,
):
    components = rail_sums.shape[1]
    bootstrap_indices = rng.integers(
        0,
        components,
        size=(BOOTSTRAP_SAMPLES, components),
    )
    rail_bootstrap = np.empty((BOOTSTRAP_SAMPLES, len(time_min)), dtype=float)
    off_rail_bootstrap = np.empty_like(rail_bootstrap)
    baseline = time_min <= BASELINE_MINUTES

    for bootstrap_index, sampled_components in enumerate(bootstrap_indices):
        rail_intensity = (
            rail_sums[:, sampled_components].sum(axis=1)
            / rail_counts[sampled_components].sum()
        )
        off_rail_intensity = (
            off_rail_sums[:, sampled_components].sum(axis=1)
            / off_rail_counts[sampled_components].sum()
        )
        rail_bootstrap[bootstrap_index] = (
            rail_intensity / rail_intensity[baseline].mean()
        )
        off_rail_bootstrap[bootstrap_index] = (
            off_rail_intensity / off_rail_intensity[baseline].mean()
        )

    rail_bootstrap = centered_rolling_mean_matrix(time_min, rail_bootstrap)
    off_rail_bootstrap = centered_rolling_mean_matrix(
        time_min,
        off_rail_bootstrap,
    )
    observed_rail = centered_rolling_mean(time_min, observed_rail)
    observed_off_rail = centered_rolling_mean(time_min, observed_off_rail)

    tail = (1.0 - CONFIDENCE_LEVEL) * 50.0
    rail_ci = np.percentile(rail_bootstrap, [tail, 100.0 - tail], axis=0)
    off_rail_ci = np.percentile(
        off_rail_bootstrap,
        [tail, 100.0 - tail],
        axis=0,
    )

    observed_difference = observed_rail - observed_off_rail
    bootstrap_difference = rail_bootstrap - off_rail_bootstrap
    difference_se = np.std(bootstrap_difference, axis=0, ddof=1)
    if np.any(difference_se == 0):
        raise ValueError("Bootstrap difference standard error must be positive")
    cluster_test = cluster_mass_test(
        observed_difference,
        bootstrap_difference,
        difference_se,
    )

    return {
        "bootstrap_indices": bootstrap_indices,
        "rail_bootstrap": rail_bootstrap.astype(np.float32),
        "off_rail_bootstrap": off_rail_bootstrap.astype(np.float32),
        "rail_smoothed": observed_rail,
        "off_rail_smoothed": observed_off_rail,
        "rail_ci_lower": rail_ci[0],
        "rail_ci_upper": rail_ci[1],
        "off_rail_ci_lower": off_rail_ci[0],
        "off_rail_ci_upper": off_rail_ci[1],
        "difference": observed_difference,
        "difference_se": difference_se,
        **cluster_test,
    }


def build_component_cache(primary_cache):
    component_cache = {}
    for recording in ["off_to_on", "on_to_off"]:
        (
            rail_labels,
            off_rail_labels,
            rail_counts,
            off_rail_counts,
        ) = component_geometry(
            primary_cache[f"{recording}_rail_mask"],
            primary_cache[f"{recording}_off_rail_mask"],
        )
        rail_sums, off_rail_sums = measure_component_time_courses(
            recording,
            rail_labels,
            off_rail_labels,
        )
        values = {
            "rail_labels": rail_labels,
            "off_rail_labels": off_rail_labels,
            "rail_counts": rail_counts,
            "off_rail_counts": off_rail_counts,
            "rail_sums": rail_sums,
            "off_rail_sums": off_rail_sums,
        }
        component_cache.update(
            {
                f"{recording}_{name}": value
                for name, value in values.items()
            }
        )
    component_cache["parallel_workers"] = np.asarray(PARALLEL_WORKERS)
    np.savez_compressed(COMPONENT_CACHE_PATH, **component_cache)


def build_bootstrap_cache(primary_cache, component_cache):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    bootstrap_cache = {}
    for recording in ["off_to_on", "on_to_off"]:
        result = bootstrap_recording(
            primary_cache[f"{recording}_time_min"],
            primary_cache[f"{recording}_rail_ff0"],
            primary_cache[f"{recording}_off_rail_ff0"],
            component_cache[f"{recording}_rail_sums"],
            component_cache[f"{recording}_off_rail_sums"],
            component_cache[f"{recording}_rail_counts"],
            component_cache[f"{recording}_off_rail_counts"],
            rng,
        )
        bootstrap_cache.update(
            {
                f"{recording}_{name}": value
                for name, value in result.items()
            }
        )

    bootstrap_cache.update(
        {
            "bootstrap_samples": np.asarray(BOOTSTRAP_SAMPLES),
            "bootstrap_seed": np.asarray(BOOTSTRAP_SEED),
            "confidence_level": np.asarray(CONFIDENCE_LEVEL),
            "cluster_forming_z": np.asarray(CLUSTER_FORMING_Z),
            "triple_star_p": np.asarray(TRIPLE_STAR_P),
            "rolling_window_seconds": np.asarray(ROLLING_WINDOW_SECONDS),
            "inference_method": np.asarray("cluster_mass_bootstrap_v1"),
        }
    )
    np.savez_compressed(BOOTSTRAP_CACHE_PATH, **bootstrap_cache)


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


def significant_runs(significant):
    changes = np.diff(np.pad(significant.astype(int), (1, 1)))
    starts = np.flatnonzero(changes == 1)
    stops = np.flatnonzero(changes == -1) - 1
    return zip(starts, stops)


def plot_fluorescence_dynamics(cache, bootstrap_cache):
    setup_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.5), sharey=True)
    panels = [
        (
            "off_to_on",
            "OFF-to-ON",
            COLORS["off_to_on_rail"],
            COLORS["off_to_on_off_rail"],
        ),
        (
            "on_to_off",
            "ON-to-OFF",
            COLORS["on_to_off_rail"],
            COLORS["on_to_off_off_rail"],
        ),
    ]
    plotted_values = []
    for ax, (recording, title, rail_color, off_rail_color) in zip(axes, panels):
        time_min = cache[f"{recording}_time_min"]
        rail_values = bootstrap_cache[f"{recording}_rail_smoothed"]
        off_rail_values = bootstrap_cache[f"{recording}_off_rail_smoothed"]
        rail_ci_lower = bootstrap_cache[f"{recording}_rail_ci_lower"]
        rail_ci_upper = bootstrap_cache[f"{recording}_rail_ci_upper"]
        off_rail_ci_lower = bootstrap_cache[f"{recording}_off_rail_ci_lower"]
        off_rail_ci_upper = bootstrap_cache[f"{recording}_off_rail_ci_upper"]
        plotted_values.extend(
            [
                rail_ci_lower,
                rail_ci_upper,
                off_rail_ci_lower,
                off_rail_ci_upper,
            ]
        )

        ax.fill_between(
            time_min,
            rail_ci_lower,
            rail_ci_upper,
            color=rail_color,
            alpha=0.18,
            linewidth=0,
        )
        ax.fill_between(
            time_min,
            off_rail_ci_lower,
            off_rail_ci_upper,
            color=off_rail_color,
            alpha=0.25,
            linewidth=0,
        )
        ax.plot(
            time_min,
            rail_values,
            color=rail_color,
            linestyle="-",
            label="Rail",
        )
        ax.plot(
            time_min,
            off_rail_values,
            color=off_rail_color,
            linestyle="-",
            label="Off rail",
        )
        xmax = float(time_min[-1])
        ax.set_xlim(0, xmax)
        ax.set_xticks([0, xmax])
        ax.set_xlabel("Time (min)")
        ax.set_title(title)
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(0.0, 1.0),
            fontsize=8,
            frameon=False,
        )
        ax.set_box_aspect(1)

    all_values = np.concatenate(plotted_values)
    value_min = float(np.nanmin(all_values))
    value_max = float(np.nanmax(all_values))
    value_span = value_max - value_min
    y_min = max(0.0, np.floor((value_min - 0.05 * value_span) * 10.0) / 10.0)
    y_max = np.ceil((value_max + 0.25 * value_span) * 10.0) / 10.0
    significance_y = value_max + 0.07 * value_span
    star_y = value_max + 0.08 * value_span

    for ax, (recording, _, _, _) in zip(axes, panels):
        time_min = cache[f"{recording}_time_min"]
        significant = bootstrap_cache[f"{recording}_triple_significant"]
        runs = list(significant_runs(significant))
        for start, stop in runs:
            ax.plot(
                [time_min[start], time_min[stop]],
                [significance_y, significance_y],
                color="black",
                linewidth=2,
                solid_capstyle="butt",
            )
            ax.text(
                (time_min[start] + time_min[stop]) / 2.0,
                star_y,
                "***",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        if not runs:
            ax.plot(
                [time_min[0], time_min[-1]],
                [significance_y, significance_y],
                color="black",
                linewidth=2,
                solid_capstyle="butt",
            )
            ax.text(
                (time_min[0] + time_min[-1]) / 2.0,
                star_y,
                "NS",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        ax.set_ylim(y_min, y_max)
        ax.set_yticks([y_min, y_max])
        sns.despine(ax=ax, trim=True, offset=10)

    axes[0].set_ylabel(r"$F/F_0$")
    fig.subplots_adjust(wspace=0.32)
    fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)


if not CACHE_PATH.exists():
    build_cache()

with np.load(CACHE_PATH) as cache:
    if not COMPONENT_CACHE_PATH.exists():
        build_component_cache(cache)
    with np.load(COMPONENT_CACHE_PATH) as component_cache:
        if not BOOTSTRAP_CACHE_PATH.exists():
            build_bootstrap_cache(cache, component_cache)
        with np.load(BOOTSTRAP_CACHE_PATH) as bootstrap_cache:
            plot_fluorescence_dynamics(cache, bootstrap_cache)
