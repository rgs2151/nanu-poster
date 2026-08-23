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
- Plot the four normalized traces together in `plots/fluorescence_dynamics.pdf`.

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
- Cache: `cache/fluorescence_dynamics.npz`, containing fixed masks, rail references, processed references, thresholds, reference-frame indices, time axes, raw regional means, `F0` values, normalized traces, saturation fractions, and all fixed analysis parameters.
- Output: `plots/fluorescence_dynamics.pdf`.

## Statistics

- None; this output is descriptive.
- Descriptive summaries: mean regional motor intensity at every timepoint, the first-five-minute mean `F0`, the normalized ratio `F/F0`, and a centered 30-second rolling mean for display.
- Directional hypothesis for ON-to-OFF: rail motor `F/F0` decreases over time.
- Directional hypothesis for OFF-to-ON: rail motor `F/F0` increases over time.
- No null distribution, inferential threshold, model, confidence interval, or statistical test is used at this stage.
- The two recordings are single experiments rather than biological replicates, so pixels and frames are not treated as independent experimental replicates.

## Legends

- X axis: time after the first stored timepoint in minutes.
- Y axis: motor fluorescence normalized to the first-five-minute regional baseline, `F/F0`.
- Color/value: OFF-to-ON is a red family, with dark red (`#991B1B`) for rail and light red (`#E8A6A6`) for off rail. ON-to-OFF is a green family, with dark green (`#166534`) for rail and light green (`#86C995`) for off rail.
- Grouping: color family identifies the transition and color darkness identifies rail versus off rail.
- Ordering/sorting: timepoints remain in acquisition order.
- Lines/markers/labels: four solid lines without markers or horizontal reference lines; the legend is frameless.
- Panels: one panel containing all four time courses and no title.

## Interpretation

- The OFF-to-ON rail trace rises to about 1.8 times its first-five-minute baseline, whereas its off-rail trace reaches about 1.1. The much larger rail-region change is the visually dominant result.
- The ON-to-OFF rail and off-rail traces both remain close to their own baselines. Their last-five-minute means are approximately 1.02 and 0.99, respectively, so this recording does not show a comparable sustained regional change.
- The separation between the OFF-to-ON rail and off-rail traces indicates that the large motor-fluorescence increase is concentrated in the DNA-defined rail region rather than shared equally by nearby non-rail pixels.
- These traces describe two individual recordings and do not establish population-level reproducibility, molecular binding below optical resolution, or statistical significance.

## Notes

- The cache is reused whenever present so plotting and documentation changes do not reread or resegment the TIFF stacks. Delete the cache only when an explicit recomputation is required.
- Raw regional means are cached as well as normalized traces, so a later normalization change can be calculated without rereading the source TIFFs.
- The plotted lines use a centered 30-second rolling mean. Unsmoothed normalized traces and raw regional means remain in the cache; no background subtraction, null distribution, or statistical trend calculation is applied.
- The ON-to-OFF `F0` values are 639.4 detector units on rail and 555.9 off rail. The OFF-to-ON values are 16,794.4 on rail and 15,299.9 off rail.
- Saturated motor pixels are retained in the regional means, and their fractions are cached. No ON-to-OFF pixels in either region are saturated. In OFF-to-ON, the rail-region saturated fraction reaches 9.2% and averages 4.0%; because clipped values are lower bounds on the underlying signal, the measured rail increase is conservative at affected timepoints.
- The completed `parking/vis` unit remains frozen.

## References

- Waters, J. C. (2009). Accuracy and precision in quantitative fluorescence microscopy. *Journal of Cell Biology*, 185(7), 1135–1148. https://doi.org/10.1083/jcb.200903097
- Otsu, N. (1979). A threshold selection method from gray-level histograms. *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66. https://doi.org/10.1109/TSMC.1979.4310076
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
