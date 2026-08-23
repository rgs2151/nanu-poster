# fluorescence_dynamics

**Research question:** Does the motor fluorescence specifically associated with DNA rails increase or decrease over time?

## Method

- Load the single ON-to-OFF and single OFF-to-ON recordings and preserve the pairing between each motor image and its DNA-rail image.
- For each recording, build one rail reference as the pixelwise temporal median of 101 evenly spaced DNA-channel timepoints.
- Smooth the reference with a one-pixel Gaussian kernel, subtract a broad Gaussian background with sigma 12 pixels, and apply Otsu's automatic threshold.
- Remove connected detections smaller than 12 pixels, close one-pixel gaps, fill holes smaller than 12 pixels, and retain the observed rail width rather than reducing rails to centerlines.
- Define the rail region as the DNA-derived mask expanded by two pixels. This fixed expansion is part of the rail definition and provides the approved tolerance for optical width and minor registration offsets.
- Define the off-rail comparison region as the band beginning four pixels and ending ten pixels outside the expanded rail region. Freeze both regions for the full recording; motor brightness does not define or move them.
- At each timepoint, calculate the mean raw motor-channel intensity separately across all rail pixels and all off-rail pixels. Do not subtract one region from the other.
- Define `F0` separately for every recording-region pair as its mean intensity during the first five minutes, then divide that pair's full intensity trace by its own `F0`.
- Keep every timepoint in acquisition order and apply a centered 30-second rolling mean to each normalized trace for display. At each plotted timepoint, average the observations within 15 seconds before and after it; use the available observations at the recording edges.
- Label the fixed rail mask into connected spatial structures: 17 in OFF-to-ON and 16 in ON-to-OFF. Assign every off-rail pixel to its nearest connected rail structure so each structure contributes a paired rail and off-rail time course.
- Draw 1,000 bootstrap samples of the connected structures with replacement. When a structure is drawn, retain all its timepoints and both of its paired regions; aggregate sampled pixel sums and counts, recalculate each sampled trace's `F0`, and apply the same 30-second rolling mean.
- Use the 2.5th and 97.5th percentiles of the 1,000 sampled traces as pointwise 95% confidence intervals.
- Compare rail minus off rail with a two-sided temporal cluster-mass bootstrap that controls repeated testing across the time axis. Display only areas with family-wise-error-corrected `p <= 0.001`.
- Plot OFF-to-ON on the left and ON-to-OFF on the right in `plots/fluorescence_dynamics.pdf`.

## Variables

- Data/input: `data/on_to_off.tif` and `data/off_to_on.tif`.
- Recording labels: ON-to-OFF and OFF-to-ON.
- Rail-defining signal: DNA fluorescence only.
- Rail region: segmented DNA rails plus a two-pixel expansion.
- Off-rail region: nearby pixels 4–10 pixels outside the expanded rail region.
- Motor fluorescence `F(t)`: mean raw motor-channel detector intensity within one fixed region at time `t`.
- Baseline `F0`: mean regional motor intensity over timepoints at or before five minutes, calculated separately for all four traces.
- Normalized fluorescence: `F(t) / F0`.
- Display smoothing: centered 30-second rolling mean applied separately to each normalized trace.
- Time: exact embedded elapsed time for ON-to-OFF; timepoint index multiplied by 2.188 seconds for OFF-to-ON.
- Detector diagnostic: the fraction of pixels in each region equal to the 16-bit maximum of 65,535 at every timepoint.
- Resampling units: 17 connected rail structures in OFF-to-ON and 16 in ON-to-OFF.
- Bootstrap settings: 1,000 paired cluster resamples with replacement, random seed 2,151, and 95% pointwise percentile intervals.
- Cluster-forming threshold: absolute standardized rail-minus-off-rail difference at least 1.96.
- Multiple-testing threshold: cluster-level family-wise-error-corrected `p <= 0.001`, displayed as `p < 0.001`.
- Primary cache: `cache/fluorescence_dynamics.npz`, containing fixed masks, rail references, processed references, thresholds, reference-frame indices, time axes, raw regional means, `F0` values, normalized traces, saturation fractions, and fixed analysis parameters.
- Component cache: `cache/fluorescence_components.npz`, containing component label images, pixel counts, and motor-intensity sums for every structure, region, and timepoint.
- Bootstrap cache: `cache/fluorescence_bootstrap.npz`, containing all resample indices, 1,000 sampled traces per region and recording, confidence limits, observed differences, bootstrap standard errors, null maximum cluster masses, cluster boundaries, corrected cluster `p` values, significance masks, random seed, thresholds, and smoothing settings.
- Output: `plots/fluorescence_dynamics.pdf`.

## Statistics

- Test: paired connected-structure bootstrap with a two-sided maximum temporal cluster-mass correction.
- Null hypothesis: after accounting for variation among connected rail structures, rail and off-rail `F/F0` do not differ over any temporally contiguous area.
- Alternative hypothesis: rail and off-rail `F/F0` differ over at least one temporally contiguous area.
- Repeated measurements: resample whole connected structures rather than pixels or frames. Every selected structure carries its complete time course and paired rail/off-rail regions into a bootstrap sample.
- Pointwise statistic: the smoothed rail-minus-off-rail difference divided by its bootstrap standard error.
- Cluster statistic: the sum of the absolute pointwise statistics across adjacent timepoints exceeding 1.96.
- Null distribution: center each bootstrap difference on the observed difference, find the largest cluster mass in each of 1,000 resamples, and compare every observed cluster with that maximum-mass distribution.
- Multiple comparisons: using the largest null cluster in each resample controls the family-wise error rate over the full time axis within each recording.
- Cluster `p` value: `(1 + number of null maximum cluster masses at least as large as the observed mass) / 1,001`. The smallest attainable value is `1/1,001 = 0.000999`.
- Decision rule: draw a black bar and `p < 0.001` for corrected cluster `p <= 0.001`; when no cluster meets that threshold, draw a full-width black bar labeled `N.S`.
- Confidence intervals: pointwise 95% percentile intervals from the 1,000 paired connected-structure bootstrap samples.
- Scope: the uncertainty and test describe variation across segmented structures within each single field of view. They are not biological-replicate confidence intervals or population-level evidence.

## Legends

- X axis: time after the first stored timepoint in minutes.
- Y axis: motor fluorescence normalized to the first-five-minute regional baseline, `F/F0`; the shared display range ends at 2.7 to leave clear space above the annotations.
- Color/value: OFF-to-ON uses dark red (`#991B1B`) for rail and light red (`#E8A6A6`) for off rail. ON-to-OFF uses dark green (`#166534`) for rail and light green (`#86C995`) for off rail.
- Grouping: each panel has a two-entry legend containing only `Rail` and `Off rail`; color darkness identifies the region.
- Ordering/sorting: timepoints remain in acquisition order.
- Lines/markers/labels: solid lines show the 30-second rolling means and translucent bands show pointwise 95% bootstrap confidence intervals. A black bar is labeled `p < 0.001` for the corrected OFF-to-ON cluster or with a small `N.S` when no cluster meets the display threshold. Annotation heights are set independently so the ON-to-OFF bar sits just above its confidence bands while both legends remain clearly separated above. There are no baseline reference lines.
- Panels: one row by two columns; OFF-to-ON is left and ON-to-OFF is right. The y axis is shared.

## Interpretation

- The OFF-to-ON rail trace rises to about 1.8 times its first-five-minute baseline, whereas its off-rail trace reaches about 1.1. The much larger rail-region change is the visually dominant result.
- The ON-to-OFF rail and off-rail traces both remain close to their own baselines. Their last-five-minute means are approximately 1.02 and 0.99, respectively, so this recording does not show a comparable sustained regional change.
- The separation between the OFF-to-ON rail and off-rail traces indicates that the large motor-fluorescence increase is concentrated in the DNA-defined rail region rather than shared equally by nearby non-rail pixels.
- OFF-to-ON has one corrected temporal cluster from 5.43 to 76.14 minutes with `p = 0.000999`, displayed as `p < 0.001`.
- ON-to-OFF has no temporal cluster meeting the `p <= 0.001` display threshold and is labeled `N.S`.
- These traces describe two individual recordings. The within-recording cluster test does not establish population-level reproducibility, biological-replicate significance, or molecular binding below optical resolution.

## Notes

- The primary, component, and bootstrap caches are reused whenever present. Plot-only changes do not reread TIFFs, recompute component measurements, or rerun the 1,000 resamples.
- Raw regional means are cached as well as normalized traces, so a later normalization change can be calculated without rereading the source TIFFs.
- The plotted lines use a centered 30-second rolling mean. Unsmoothed normalized traces and raw regional means remain cached; no background subtraction or separate trend-direction test is applied.
- The component reduction uses all 64 available CPU workers. Its output is cached separately so later resampling-method changes do not reread the TIFFs.
- Confidence-interval width reflects heterogeneity among connected rail structures within a recording; it must not be interpreted as variation across biological experiments.
- The ON-to-OFF `F0` values are 639.4 detector units on rail and 555.9 off rail. The OFF-to-ON values are 16,794.4 on rail and 15,299.9 off rail.
- Saturated motor pixels are retained in the regional means, and their fractions are cached. No ON-to-OFF pixels in either region are saturated. In OFF-to-ON, the rail-region saturated fraction reaches 9.2% and averages 4.0%; because clipped values are lower bounds on the underlying signal, the measured rail increase is conservative at affected timepoints.
- The completed `parking/vis` unit remains frozen.

## References

- Waters, J. C. (2009). Accuracy and precision in quantitative fluorescence microscopy. *Journal of Cell Biology*, 185(7), 1135–1148. https://doi.org/10.1083/jcb.200903097
- Otsu, N. (1979). A threshold selection method from gray-level histograms. *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66. https://doi.org/10.1109/TSMC.1979.4310076
- Cheng, G., Yu, Z., & Huang, J. Z. (2013). The cluster bootstrap consistency in generalized estimating equations. *Journal of Multivariate Analysis*, 115, 33–47. https://doi.org/10.1016/j.jmva.2012.09.003
- Maris, E., & Oostenveld, R. (2007). Nonparametric statistical testing of EEG- and MEG-data. *Journal of Neuroscience Methods*, 164(1), 177–190. https://doi.org/10.1016/j.jneumeth.2007.03.024
- `data/README.md` for channel mapping, time calibration, and replication constraints.
- `DECISIONS.md` for shared definitions of time and rail regions.
- `STYLE.md` for the required plot appearance.

# segmentation_diagnostic

## Method

- Load `data/off_to_on.tif` without changing the source file and verify its two-channel `ZCYX` layout.
- Select one timepoint reproducibly with random seed 2,151. The selected zero-based timepoint is 1,297, but the frame number is intentionally omitted from the figure because it is not part of the comparison.
- Build a stable rail reference as the pixelwise temporal median of 101 evenly spaced DNA-rail timepoints spanning the recording.
- Smooth the rail reference with a one-pixel Gaussian kernel, subtract a broad Gaussian background with sigma 12 pixels, and apply Otsu's automatic threshold.
- Remove connected detections smaller than 12 pixels, close one-pixel gaps, fill holes smaller than 12 pixels, and expand the resulting rail mask by two pixels.
- Define the off-rail comparison region as a band beginning four pixels and ending ten pixels outside the expanded rail region.
- Apply the fixed DNA-derived mask directly to the paired motor channel because both channels in this TIFF share the same pixel coordinates.
- Calculate the descriptive rail-minus-off-rail excess as the mean motor intensity inside the rail region minus the median motor intensity in the off-rail region.
- Write `plots/segmentation_diagnostic.pdf` with raw, processed, masked, projected, and intensity-comparison views.

## Variables

- Data/input: `data/off_to_on.tif`.
- Selected observation: zero-based timepoint 1,297, selected with random seed 2,151.
- Rail channel: channel 0.
- Motor channel: channel 1.
- Rail reference: temporal median of 101 evenly spaced rail-channel timepoints.
- Smoothing sigma: 1 pixel.
- Broad-background sigma: 12 pixels.
- Threshold: Otsu threshold calculated from the processed rail reference.
- Minimum retained object and filled-hole size: 12 pixels.
- Rail-mask expansion: 2 pixels.
- Off-rail region: 4–10 pixels outside the expanded rail region.
- Measurement: mean rail motor intensity minus median off-rail motor intensity, in raw detector intensity units.
- Saturation diagnostic: fraction of rail-mask motor pixels equal to the 16-bit detector maximum of 65,535.
- Output: `parking/fluorescence_dynamics/plots/segmentation_diagnostic.pdf`.

## Statistics

- None; this output is descriptive.
- Descriptive summaries: the motor-intensity distributions in the rail and off-rail regions, their reference lines, the rail-minus-off-rail excess, and the fraction of rail pixels at the detector maximum.
- No null hypothesis, alternative hypothesis, inferential threshold, model, or statistical test is used.
- Pixel values are spatially related measurements within one frame and are not treated as independent experimental replicates.

## Legends

- X axis: image x-coordinate in pixels for image panels, with labels hidden; raw motor intensity in arbitrary detector units for the distribution panel.
- Y axis: image y-coordinate in pixels for image panels, with labels hidden; probability density for the distribution panel.
- Color/value: grayscale is recorded or processed fluorescence intensity; dark red identifies the rail region or its motor values; midnight blue identifies the off-rail region or its motor values.
- Grouping: one selected OFF-to-ON timepoint plus the fixed rail reference built from the same recording.
- Ordering/sorting: raw and processed rail diagnostics occupy the top row; motor projection and measurement diagnostics occupy the bottom row.
- Lines/markers/labels: solid contours outline spatial measurement regions; dashed vertical lines mark the median off-rail and mean rail-region motor intensities.
- Panels: raw DNA rails; processed rail reference; final rail mask; rail and off-rail regions; raw motor channel; rail mask on motor; motor signal restricted to rails; motor-intensity comparison.

## Interpretation

- The raw and processed rail panels show whether denoising and broad-background subtraction preserve visible rail structures.
- The mask overlays show whether the DNA-derived region follows rails without absorbing large areas of background.
- The motor overlay and restricted-motor panel show exactly which motor pixels contribute to the proposed fluorescence measurement.
- Separation between the rail and off-rail motor distributions indicates that the selected rail region contains motor signal beyond nearby off-rail fluorescence in this diagnostic frame.
- In this selected frame, 5.1% of rail-mask motor pixels equal the 16-bit maximum of 65,535. Those pixels are clipped, so the on-rail mean is a lower bound on the underlying fluorescence and this saturation must be addressed before accepting a full quantitative time course.
- This single-frame diagnostic validates measurement geometry only; it does not establish a time trend or switching result.

## Notes

- This diagnostic is an approval gate before full fluorescence extraction.
- No full motor-fluorescence time course, `F/F0` normalization, temporal smoothing, null distribution, or statistical trend test is performed.
- The rail mask is fixed from the temporal rail reference rather than re-segmented from the selected motor frame.
- The segmentation geometry is acceptable in this diagnostic, but the detected motor-channel saturation remains an approval issue for the later `F/F0` analysis.
- If the overlay is not acceptable, mask construction will be revised before any full analysis runs.

## References

- Waters, J. C. (2009). Accuracy and precision in quantitative fluorescence microscopy. *Journal of Cell Biology*, 185(7), 1135–1148. https://doi.org/10.1083/jcb.200903097
- Otsu, N. (1979). A threshold selection method from gray-level histograms. *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66. https://doi.org/10.1109/TSMC.1979.4310076
- `data/README.md` for channel mapping and recording constraints.
