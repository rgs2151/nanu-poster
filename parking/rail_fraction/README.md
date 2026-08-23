# rail_fraction

**Research question:** Is the fluorescence change distributed across more of the rail network, or caused by only a few bright hotspots?

## Method

- Load the single OFF-to-ON and single ON-to-OFF recordings while preserving the pairing between each motor image and its DNA-rail image.
- Reuse `off_to_on_rail_mask` and `on_to_off_rail_mask` directly from the approved fluorescence-dynamics cache. Do not segment the DNA channel again and do not allow motor brightness to change the mask.
- Use the established rail definition: the fixed DNA-derived mask plus its two-pixel local expansion. The mask contains 7,918 pixels in OFF-to-ON and 6,347 pixels in ON-to-OFF.
- Reuse the established off-rail region 4–10 pixels outside the expanded rail mask only to define a motor-positive intensity threshold.
- For each recording separately, pool all raw off-rail motor pixels from its first five minutes. Set one fixed threshold equal to the pooled median plus three pooled median absolute deviations.
- At every timepoint, count all pixels inside the fixed expanded rail mask whose raw motor intensity is strictly greater than that recording's fixed threshold.
- Calculate motor-positive rail fraction as `100 × positive rail pixels / all pixels in the fixed expanded rail mask`. No connected-component filter changes this numerator.
- Apply a centered 30-second rolling mean for display while retaining the unsmoothed fraction at every recorded timepoint.
- Plot OFF-to-ON on the left and ON-to-OFF on the right in `plots/rail_fraction.pdf`.

## Variables

- Data/input: `data/off_to_on.tif` and `data/on_to_off.tif`.
- Mask input: `parking/fluorescence_dynamics/cache/fluorescence_dynamics.npz`.
- Recording labels: OFF-to-ON and ON-to-OFF.
- Rail region: the approved cached DNA-derived mask plus its two-pixel expansion; 7,918 pixels for OFF-to-ON and 6,347 pixels for ON-to-OFF.
- Threshold reference: raw motor intensities in the cached off-rail region during the first five minutes.
- OFF-to-ON threshold: baseline off-rail median 13,976 plus three times MAD 3,395, giving 24,161 detector units.
- ON-to-OFF threshold: baseline off-rail median 466 plus three times MAD 109, giving 793 detector units.
- Motor-positive pixel: a pixel inside the fixed rail region with raw motor intensity strictly greater than its recording's fixed threshold.
- Motor-positive rail fraction: percentage of the fixed rail-region pixels that are motor-positive at one timepoint.
- Display smoothing: centered 30-second rolling mean; the available timepoints are used at recording edges.
- Time: exact embedded elapsed time for ON-to-OFF; timepoint index multiplied by 2.188 seconds for OFF-to-ON.
- Compute: 64 CPU workers read disjoint timepoint chunks; GPU acceleration is not used because TIFF decoding and masked counting are the limiting operations.
- Cache: `cache/rail_fraction.npz`, containing thresholds, baseline histogram summaries, time axes, per-frame positive counts, rail-pixel counts, raw and smoothed fractions, parameter values, source-cache hash, and rail/off-rail mask hashes.
- Output: `plots/rail_fraction.pdf`.

## Statistics

- None; this output is descriptive.
- Descriptive summaries: the raw fraction at each timepoint, its centered 30-second rolling mean, and first-five-minute versus last-five-minute means.
- Null hypothesis: not tested.
- Alternative hypothesis: not tested.
- Threshold decision rule: call a rail pixel motor-positive only when its raw motor intensity is strictly greater than the recording-specific baseline off-rail median plus three median absolute deviations. This is a signal-detection rule, not a significance threshold.
- Why this measure is appropriate: it quantifies the spatial extent of above-background motor signal within the same fixed rail geometry used by the fluorescence-dynamics analysis.
- Frames and pixels are repeated observations within one field of view, not biological replicates; no confidence interval, p-value, or population-level inference is reported.

## Legends

- X axis: time after the first stored timepoint in minutes.
- Y axis: percentage of pixels in the fixed expanded rail region whose motor intensity exceeds the fixed baseline-derived threshold; the shared display range is 0–50%.
- Color/value: dark red (`#991B1B`) identifies OFF-to-ON and dark green (`#166534`) identifies ON-to-OFF.
- Grouping: one panel per recording.
- Ordering/sorting: timepoints remain in acquisition order.
- Lines/markers/labels: a thin translucent line shows every raw per-frame fraction; a dark solid line shows the centered 30-second rolling mean. There are no markers, confidence bands, or significance annotations.
- Panels: one row by two columns; OFF-to-ON is left and ON-to-OFF is right. The y axis is shared.

## Interpretation

- OFF-to-ON rises from a first-five-minute mean of 11.7% to a last-five-minute mean of 45.5%, an increase of 33.8 percentage points.
- ON-to-OFF changes from a first-five-minute mean of 23.6% to a last-five-minute mean of 19.7%, a decrease of 3.9 percentage points.
- The large OFF-to-ON increase means that the previously observed rail-fluorescence increase is distributed across a progressively larger fraction of the fixed rail region rather than being explained only by a few pixels becoming brighter.
- ON-to-OFF remains in a much narrower range and does not show a comparable expansion of motor-positive rail area.
- These are descriptive results from one recording per transition and do not establish biological reproducibility.

## Notes

- The source fluorescence-dynamics cache is read-only. Its SHA-256 hash is recorded inside the rail-fraction cache so the exact accepted mask source can be audited.
- The threshold is fixed once per recording from its initial off-rail distribution. It is not recalculated at each frame and therefore cannot follow the motor signal over time.
- The fraction records spatial coverage above threshold, not fluorescence magnitude, motor velocity, direction, or molecular binding below optical resolution.
- Saturated pixels remain motor-positive but count only once, so detector clipping cannot inflate a pixel's contribution beyond one positive pixel.
- The cache is reused whenever present, so plot-only changes do not reread the TIFFs or recalculate the per-frame counts.

## References

- Waters, J. C. (2009). Accuracy and precision in quantitative fluorescence microscopy. *Journal of Cell Biology*, 185(7), 1135–1148. https://doi.org/10.1083/jcb.200903097
- `parking/fluorescence_dynamics/README.md` for the accepted segmentation geometry and fluorescence measurement.
- `DECISIONS.md` for the shared definitions of time and rail regions.
- `data/README.md` for channel mapping and the single-recording constraint.
- `STYLE.md` for plot appearance.

# rail_fraction_diagnostic

## Method

- Load the exact rail masks, rail-reference images, thresholds, time axes, and fraction results used by `rail_fraction`.
- Display the cached temporal-median DNA reference with the boundary of the approved expanded rail region; do not create a new segmentation.
- Display the first-five-minute off-rail motor-intensity distribution used to set the fixed threshold. Mark its median with a gray dashed line and the median-plus-three-MAD threshold with a black line.
- Select an early timepoint nearest 2.5 minutes and a late timepoint nearest 2.5 minutes before the recording ends, using the same rule independently for both recordings.
- On each selected raw motor frame, color every pixel that lies inside the approved expanded rail mask and exceeds the fixed threshold. These colored pixels are the exact numerator of the displayed percentage.
- Draw hollow black circles around at most the 20 largest contiguous positive regions containing at least four pixels. The circles are visual guides only; they do not add, remove, merge, or filter counted pixels.
- Write the two-row diagnostic to `plots/rail_fraction_diagnostic.pdf`.

## Variables

- Data/input: `data/off_to_on.tif`, `data/on_to_off.tif`, the fluorescence-dynamics mask cache, and `cache/rail_fraction.npz`.
- OFF-to-ON diagnostic timepoints: index 69 at 2.52 minutes and index 2,019 at 73.63 minutes.
- ON-to-OFF diagnostic timepoints: index 72 at 2.50 minutes and index 1,934 at 73.50 minutes.
- OFF-to-ON fixed motor-positive threshold: 24,161 detector units.
- ON-to-OFF fixed motor-positive threshold: 793 detector units.
- Positive-pixel overlay: all pixels satisfying `rail mask AND motor intensity > threshold`.
- Circle guides: up to 20 largest eight-connected positive regions, each at least four pixels in area.
- Outputs: `plots/rail_fraction_diagnostic.pdf`.

## Statistics

- None; this output is a measurement audit.
- Descriptive summaries: baseline off-rail intensity density, fixed threshold, and the exact motor-positive rail fraction in each selected frame.
- Null hypothesis: not tested.
- Alternative hypothesis: not tested.
- Decision rule: the same fixed intensity threshold used by the full time course determines every colored pixel. Circle size and component ranking do not affect the measurement.
- Why this diagnostic is appropriate: it exposes the denominator geometry, the threshold source, and the exact numerator pixels needed to reproduce the rail-fraction calculation.

## Legends

- X axis: raw motor intensity in detector units for the threshold panels; image x-coordinate is hidden in the image panels.
- Y axis: probability density for the threshold panels, with tick labels hidden; image y-coordinate is hidden in the image panels.
- Color/value: grayscale shows recorded fluorescence; red outlines/overlays identify the OFF-to-ON rail region and positive pixels; green identifies the corresponding ON-to-OFF quantities; black vertical lines mark thresholds; gray dashed lines mark baseline off-rail medians.
- Grouping: OFF-to-ON occupies the top row and ON-to-OFF the bottom row.
- Ordering/sorting: each row shows the reused rail region, threshold distribution, early motor frame, and late motor frame from left to right.
- Lines/markers/labels: colored pixels are the exact fraction numerator; hollow black circles point to the largest contiguous positive regions; percentages above motor frames are recalculated directly from the displayed pixels.
- Panels: two rows by four columns.

## Interpretation

- The colored outlines confirm that both measurements use the exact expanded rail geometry accepted in the fluorescence-dynamics analysis.
- The threshold panels show that each recording has one fixed threshold derived before the time-course fraction is calculated.
- OFF-to-ON increases from 10.9% positive pixels at 2.52 minutes to 44.6% at 73.63 minutes, with positive pixels spreading along multiple rail structures.
- ON-to-OFF changes from 23.3% positive pixels at 2.50 minutes to 20.0% at 73.50 minutes and does not show comparable spatial expansion.
- The diagnostic supports the geometry and counting logic but is not a separate statistical test.

## Notes

- Every colored pixel contributes exactly one count regardless of its brightness above threshold.
- The black circles are deliberately limited to preserve readability; uncircled colored pixels still contribute to the displayed percentage and the full time course.
- Early and late frames are fixed by time, not selected for unusually high or low fraction values.

## References

- Otsu, N. (1979). A threshold selection method from gray-level histograms. *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66. https://doi.org/10.1109/TSMC.1979.4310076
- Waters, J. C. (2009). Accuracy and precision in quantitative fluorescence microscopy. *Journal of Cell Biology*, 185(7), 1135–1148. https://doi.org/10.1083/jcb.200903097
- `parking/fluorescence_dynamics/README.md` for the accepted segmentation procedure.
- `DECISIONS.md` for the project-wide rail-region definition.
