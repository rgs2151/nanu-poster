from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tifffile
from skimage import filters, morphology


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "off_to_on.tif"
OUTPUT_PATH = Path(__file__).resolve().parent / "plots" / "segmentation_diagnostic.pdf"

RANDOM_SEED = 2151
REFERENCE_TIMEPOINTS = 101
SMOOTHING_SIGMA = 1.0
BACKGROUND_SIGMA = 12.0
MINIMUM_OBJECT_SIZE = 12
MASK_EXPANSION_RADIUS = 2
BACKGROUND_INNER_RADIUS = 4
BACKGROUND_OUTER_RADIUS = 10

with tifffile.TiffFile(DATA_PATH) as tif:
    series = tif.series[0]
    if series.axes != "ZCYX" or series.shape[1] != 2:
        raise ValueError(
            f"Expected a two-channel ZCYX stack, found {series.axes} {series.shape}"
        )

    rng = np.random.default_rng(RANDOM_SEED)
    timepoint_index = int(rng.integers(0, series.shape[0]))
    reference_indices = np.linspace(
        0,
        series.shape[0] - 1,
        REFERENCE_TIMEPOINTS,
        dtype=int,
    )
    rail_stack = np.stack(
        [tif.pages[index * 2].asarray() for index in reference_indices]
    )
    rail_frame = tif.pages[timepoint_index * 2].asarray()
    motor_frame = tif.pages[timepoint_index * 2 + 1].asarray()

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

background_inner = morphology.dilation(
    rail_mask,
    morphology.disk(BACKGROUND_INNER_RADIUS),
)
background_outer = morphology.dilation(
    rail_mask,
    morphology.disk(BACKGROUND_OUTER_RADIUS),
)
background_band = background_outer & ~background_inner

motor_values_on_rails = motor_frame[rail_mask].astype(float)
motor_values_background = motor_frame[background_band].astype(float)
local_background = float(np.median(motor_values_background))
on_rail_excess = float(np.mean(motor_values_on_rails) - local_background)
detector_maximum = np.iinfo(motor_frame.dtype).max
rail_saturated_fraction = float(
    np.mean(motor_values_on_rails == detector_maximum)
)

rail_limits = np.percentile(rail_frame, [1.0, 99.8])
processed_limits = np.percentile(processed_reference, [1.0, 99.8])
motor_limits = np.percentile(motor_frame, [1.0, 99.8])
masked_motor = np.where(rail_mask, motor_frame, motor_limits[0])

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
plt.rcParams["savefig.facecolor"] = "white"
plt.rcParams["savefig.transparent"] = False

fig, axes = plt.subplots(2, 4, figsize=(12.5, 6.2))

axes[0, 0].imshow(
    rail_frame,
    cmap="gray",
    vmin=rail_limits[0],
    vmax=rail_limits[1],
)
axes[0, 0].set_title("Raw DNA rails")

axes[0, 1].imshow(
    processed_reference,
    cmap="gray",
    vmin=processed_limits[0],
    vmax=processed_limits[1],
)
axes[0, 1].set_title("Processed rail reference")

axes[0, 2].imshow(
    rail_frame,
    cmap="gray",
    vmin=rail_limits[0],
    vmax=rail_limits[1],
)
axes[0, 2].contour(rail_mask, levels=[0.5], colors="darkred", linewidths=0.8)
axes[0, 2].set_title("Final rail mask")

axes[0, 3].imshow(
    rail_frame,
    cmap="gray",
    vmin=rail_limits[0],
    vmax=rail_limits[1],
)
axes[0, 3].contour(rail_mask, levels=[0.5], colors="darkred", linewidths=0.8)
axes[0, 3].contour(
    background_band,
    levels=[0.5],
    colors="midnightblue",
    linewidths=0.6,
)
axes[0, 3].set_title("Rail and local background")

axes[1, 0].imshow(
    motor_frame,
    cmap="gray",
    vmin=motor_limits[0],
    vmax=motor_limits[1],
)
axes[1, 0].set_title("Raw motor channel")

axes[1, 1].imshow(
    motor_frame,
    cmap="gray",
    vmin=motor_limits[0],
    vmax=motor_limits[1],
)
axes[1, 1].contour(rail_mask, levels=[0.5], colors="darkred", linewidths=0.8)
axes[1, 1].set_title("Rail mask on motor")

axes[1, 2].imshow(
    masked_motor,
    cmap="gray",
    vmin=motor_limits[0],
    vmax=motor_limits[1],
)
axes[1, 2].set_title("Motor signal on rails")

combined_values = np.concatenate(
    [motor_values_on_rails, motor_values_background]
)
histogram_limits = np.percentile(combined_values, [0.5, 99.5])
histogram_bins = np.linspace(histogram_limits[0], histogram_limits[1], 45)
axes[1, 3].hist(
    motor_values_background,
    bins=histogram_bins,
    density=True,
    histtype="step",
    color="midnightblue",
    linewidth=1.2,
    label="Local background",
)
axes[1, 3].hist(
    motor_values_on_rails,
    bins=histogram_bins,
    density=True,
    histtype="step",
    color="darkred",
    linewidth=1.2,
    label="Rail region",
)
axes[1, 3].axvline(local_background, color="midnightblue", linestyle="--")
axes[1, 3].axvline(
    np.mean(motor_values_on_rails),
    color="darkred",
    linestyle="--",
)
axes[1, 3].set_title("Motor intensity comparison")
axes[1, 3].set_xlabel("Motor intensity (a.u.)")
axes[1, 3].set_ylabel("Density")
axes[1, 3].set_xlim(histogram_limits)
axes[1, 3].set_xticks(histogram_limits)
axes[1, 3].set_ylim(bottom=0)
axes[1, 3].set_yticks([0, axes[1, 3].get_ylim()[1]])
axes[1, 3].legend(loc="upper right", fontsize=7)
axes[1, 3].text(
    0.98,
    0.68,
    f"On-rail excess = {on_rail_excess:.0f} a.u.",
    transform=axes[1, 3].transAxes,
    ha="right",
    va="top",
    fontsize=8,
)
axes[1, 3].text(
    0.98,
    0.56,
    f"Rail pixels at detector maximum = {rail_saturated_fraction:.1%}",
    transform=axes[1, 3].transAxes,
    ha="right",
    va="top",
    fontsize=8,
)
sns.despine(ax=axes[1, 3], trim=True, offset=10)

for ax in axes.flat[:-1]:
    ax.set_axis_off()
for ax in axes.flat:
    ax.set_box_aspect(1)

fig.subplots_adjust(
    left=0.04,
    right=0.98,
    bottom=0.11,
    top=0.92,
    hspace=0.28,
    wspace=0.30,
)
fig.savefig(OUTPUT_PATH, bbox_inches="tight", facecolor="white", transparent=False)
plt.close(fig)
