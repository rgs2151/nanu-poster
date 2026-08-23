from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tifffile
from matplotlib.colors import ListedColormap
from matplotlib.patches import Circle
from skimage import measure

from rail_fraction import (
    CACHE_PATH,
    COLORS,
    OFF_TO_ON_PATH,
    ON_TO_OFF_PATH,
    SOURCE_CACHE_PATH,
    build_cache,
    load_motor_frame,
    setup_style,
)


UNIT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = UNIT_DIR / "plots" / "rail_fraction_composite.pdf"
EARLY_TIME_MINUTES = 2.5
LATE_WINDOW_OFFSET_MINUTES = 2.5
MINIMUM_CIRCLE_AREA = 4
MAXIMUM_CIRCLES = 20


def add_positive_overlay(ax, positive_mask, color):
    overlay = np.ma.masked_where(~positive_mask, positive_mask)
    ax.imshow(
        overlay,
        cmap=ListedColormap([color]),
        alpha=0.72,
        interpolation="none",
    )

    regions = sorted(
        measure.regionprops(measure.label(positive_mask, connectivity=2)),
        key=lambda region: region.area,
        reverse=True,
    )
    for region in regions[:MAXIMUM_CIRCLES]:
        if region.area < MINIMUM_CIRCLE_AREA:
            continue
        min_row, min_col, max_row, max_col = region.bbox
        radius = max(max_row - min_row, max_col - min_col) / 2.0 + 2.0
        row, col = region.centroid
        ax.add_patch(
            Circle(
                (col, row),
                radius=radius,
                fill=False,
                edgecolor="black",
                linewidth=0.7,
            )
        )


def plot_motor_frame(ax, motor_frame, rail_mask, threshold, color, label, limits):
    positive_mask = rail_mask & (motor_frame > threshold)
    fraction = 100.0 * np.count_nonzero(positive_mask) / np.count_nonzero(rail_mask)
    ax.imshow(
        motor_frame,
        cmap="gray",
        vmin=limits[0],
        vmax=limits[1],
        interpolation="none",
    )
    add_positive_overlay(ax, positive_mask, color)
    ax.set_title(f"{label}\n{fraction:.0f}% positive", fontsize=9)
    ax.set_axis_off()


def plot_time_course(ax, time_min, smoothed_fraction, color):
    ax.plot(
        time_min,
        smoothed_fraction,
        color=color,
        linewidth=1.4,
        label="30-second average",
    )
    xmax = float(time_min[-1])
    ax.set_xlim(0, xmax)
    ax.set_xticks([0, xmax])
    ax.set_ylim(-2.5, 52.5)
    ax.set_yticks([0, 50])
    ax.set_xlabel("Time (min)", fontsize=9)
    ax.set_ylabel("Fraction (%)", fontsize=9)
    ax.set_title(
        "Proportion of rail lit up\nby motor protein",
        fontsize=8.5,
        pad=7,
    )
    ax.legend(loc="upper left", fontsize=7, frameon=False)
    ax.tick_params(labelsize=8)
    ax.set_box_aspect(1)
    sns.despine(ax=ax, trim=True, offset=7)


def plot_composite(source_cache, cache):
    setup_style()
    fig, axes = plt.subplots(2, 4, figsize=(10.5, 6.6))
    panels = [
        ("off_to_on", "OFF-to-ON", OFF_TO_ON_PATH),
        ("on_to_off", "ON-to-OFF", ON_TO_OFF_PATH),
    ]

    for row, (recording, title, data_path) in enumerate(panels):
        color = COLORS[recording]
        rail_reference = source_cache[f"{recording}_rail_reference"]
        rail_mask = source_cache[f"{recording}_rail_mask"].astype(bool)
        time_min = cache[f"{recording}_time_min"]
        threshold = float(cache[f"{recording}_motor_positive_threshold"])
        early_index = int(np.argmin(np.abs(time_min - EARLY_TIME_MINUTES)))
        late_index = int(
            np.argmin(
                np.abs(
                    time_min
                    - (float(time_min[-1]) - LATE_WINDOW_OFFSET_MINUTES)
                )
            )
        )

        with tifffile.TiffFile(data_path) as tif:
            early_motor = load_motor_frame(tif, recording, early_index)
            late_motor = load_motor_frame(tif, recording, late_index)

        motor_limits = np.percentile(
            np.concatenate([early_motor.ravel(), late_motor.ravel()]),
            [1.0, 99.8],
        )
        rail_limits = np.percentile(rail_reference, [1.0, 99.8])

        rail_ax = axes[row, 0]
        rail_ax.imshow(
            rail_reference,
            cmap="gray",
            vmin=rail_limits[0],
            vmax=rail_limits[1],
            interpolation="none",
        )
        rail_ax.contour(
            rail_mask,
            levels=[0.5],
            colors=[color],
            linewidths=0.7,
        )
        rail_ax.set_title(title, fontsize=10)
        rail_ax.set_axis_off()

        plot_motor_frame(
            axes[row, 1],
            early_motor,
            rail_mask,
            threshold,
            color,
            "Early",
            motor_limits,
        )
        plot_motor_frame(
            axes[row, 2],
            late_motor,
            rail_mask,
            threshold,
            color,
            "Late",
            motor_limits,
        )
        plot_time_course(
            axes[row, 3],
            time_min,
            cache[f"{recording}_fraction_smoothed"],
            color,
        )

    fig.subplots_adjust(
        left=0.025,
        right=0.99,
        bottom=0.09,
        top=0.96,
        wspace=0.38,
        hspace=0.38,
    )
    fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)


if __name__ == "__main__":
    if not CACHE_PATH.exists():
        build_cache()
    with np.load(SOURCE_CACHE_PATH) as source_cache, np.load(CACHE_PATH) as cache:
        plot_composite(source_cache, cache)
