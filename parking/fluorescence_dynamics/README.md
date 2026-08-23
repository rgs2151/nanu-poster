# fluorescence_dynamics

**Research question:** Does the motor fluorescence specifically associated with DNA rails increase or decrease over time?

**Status:** Method proposal only. No segmentation, fluorescence extraction, statistical test, cache, or plot has been run. Execution requires explicit user approval.

## Method

1. Load the ON-to-OFF and OFF-to-ON recordings without changing the source TIFFs. Keep the motor-protein and DNA-rail images paired at every timepoint.
2. Use only the DNA-rail channel to decide which pixels belong to rails. Motor brightness must not influence rail detection.
3. Check spatial registration before measuring fluorescence. The DNA-derived rail outline must be overlaid on the motor view at early, middle, and late timepoints. If a fixed channel offset is present, estimate one rigid alignment for the recording, apply it to every timepoint, and freeze it before measuring the motor signal. Do not realign each frame to maximize motor overlap.
4. Correct whole-scene drift from the DNA-rail images when needed, and apply the same frame movement to the paired motor images.
5. Build one stable rail reference image per recording from the temporal median of the drift-corrected DNA-rail channel. A temporal median retains structures that persist through the recording while reducing isolated camera noise and transient bright pixels.
6. Lightly smooth the rail reference to reduce single-pixel noise, subtract broad uneven background, and apply an automatic Otsu intensity threshold to separate bright rails from dark background.
7. Remove isolated one-pixel detections and bridge only very small gaps in otherwise continuous rails. Do not skeletonize the rails because the measurement should retain their observed width.
8. Expand the segmented rail region by a small fixed number of pixels to include the optical width of motor fluorescence and tolerate a minor residual channel-registration error. The exact expansion will be chosen from mask overlays before extraction and then held fixed for both the full time course and its sensitivity check.
9. Freeze one rail mask per recording. A fixed mask prevents frame-to-frame segmentation noise or changing DNA-channel brightness from creating a false motor-fluorescence trend.
10. Define a local background band immediately around the rail mask while excluding rail pixels. For each timepoint, calculate the mean motor-channel intensity inside the rail mask and subtract the median motor-channel intensity in the local background band:

    `F(t) = mean motor intensity on rails - median local motor background`

11. Use the mean inside the rail mask rather than thresholding the motor channel into bright and dark pixels. Bright motor puncta are the signal of interest, so counting only thresholded pixels or taking the median could discard real changes. Local background subtraction keeps diffuse or spatially uneven motor fluorescence from being counted as rail-associated signal.
12. Verify rail specificity before normalization by confirming that the real rail mask contains more background-corrected motor fluorescence than the same-shaped mask shifted into nearby off-rail regions. This is a validation step, not the final result plot.
13. Define `F0` separately for each recording as the mean background-corrected rail fluorescence during the first five minutes, then calculate `F(t) / F0`. The five-minute baseline is proposed rather than approved. A multi-frame baseline is preferred to one first frame because it is less sensitive to camera noise.
14. If the OFF-to-ON baseline is indistinguishable from background, stop before dividing: a near-zero `F0` would make `F/F0` unstable and visually misleading. Bring that diagnostic back for a revised normalization decision.
15. Plot both recordings in the same panel. Use exact embedded elapsed times for ON-to-OFF and the approved 2.188-second-per-timepoint assumption for OFF-to-ON.

## Variables

- Data/input: `data/on_to_off.tif` and `data/off_to_on.tif`.
- Recording labels: ON-to-OFF and OFF-to-ON.
- Rail-defining signal: DNA-rail fluorescence only.
- Measured signal: raw motor-channel pixel intensity inside the registered DNA-derived rail mask.
- Local background: median motor-channel intensity in a surrounding off-rail band at the same timepoint.
- Rail-associated fluorescence: mean on-rail motor intensity minus median local motor background.
- Normalized fluorescence: `F(t) / F0`, calculated separately within each recording.
- Proposed baseline: the first five minutes of each recording; awaiting approval.
- Time: exact TIFF elapsed time for ON-to-OFF; timepoint index multiplied by 2.188 seconds for OFF-to-ON.
- Proposed mask behavior: one fixed mask per recording after drift correction and channel registration.
- Proposed mask expansion: a small fixed pixel radius selected from diagnostic overlays; awaiting approval.
- Planned output: `parking/fluorescence_dynamics/plots/fluorescence_dynamics.pdf`.

## Statistics

- No statistical test or null distribution has been selected or run.
- Directional hypothesis for ON-to-OFF: rail-associated motor `F/F0` decreases over time.
- Directional hypothesis for OFF-to-ON: rail-associated motor `F/F0` increases over time.
- The two recordings are single experiments, not biological replicates. Frame-level variation cannot be presented as replicate-level uncertainty or used to claim population-level significance.
- A directionality statistic and its time-series-aware null model will be proposed only after the rail mask, background correction, and `F0` definition are approved and visually validated.

## Legends

- X axis: time after the first stored timepoint in minutes.
- Y axis: background-corrected rail-associated motor fluorescence, `F/F0`.
- Color/value: dark red for ON-to-OFF and midnight blue for OFF-to-ON.
- Grouping: one line per recording in the same axes.
- Ordering/sorting: timepoints remain in acquisition order.
- Lines/markers/labels: thin lines without markers; a black dashed horizontal reference at `F/F0 = 1`; frameless legend.
- Panels: one square panel containing both time courses.
- Style: serif text, Computer-Modern math, white background, endpoint-only ticks, top and right spines removed, remaining spines trimmed and offset, and vector PDF output as specified in `STYLE.md`.
- Uncertainty: no error band, because there is only one recording for each transition.

## Interpretation

- An OFF-to-ON line that rises above its baseline supports increasing motor fluorescence within DNA-rail regions during that recording.
- An ON-to-OFF line that falls below its baseline supports decreasing motor fluorescence within DNA-rail regions during that recording.
- The analysis measures fluorescence associated with the spatial rail region; it does not by itself prove molecular binding or physical interaction below the optical resolution limit.
- Opposite time-course directions would be descriptive evidence consistent with switching, but the single recording per transition does not establish biological reproducibility.

## Notes

- Required approval before implementation: fixed versus time-varying rail mask. The proposed choice is a fixed mask per recording.
- Required approval before implementation: first-five-minute `F0`. The main risk is an OFF-to-ON baseline too close to zero.
- Required approval before extraction: visual overlay of the rail outline on both channels and the fixed mask-expansion radius.
- Required diagnostic before accepting the measurement: saturation check in the motor channel, comparison with shifted off-rail masks, and inspection of DNA-rail intensity stability for photobleaching or focus drift.
- No fluorescence smoothing is proposed for the primary line. If the raw trace is visually noisy, any temporal binning or smoothing will be discussed before use and the unsmoothed measurement will be retained.
- The completed `parking/vis` unit is frozen and is not modified by this proposal.

## References

- Waters, J. C. (2009). Accuracy and precision in quantitative fluorescence microscopy. *Journal of Cell Biology*, 185(7), 1135–1148. https://doi.org/10.1083/jcb.200903097
- Otsu, N. (1979). A threshold selection method from gray-level histograms. *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66. https://doi.org/10.1109/TSMC.1979.4310076
- `data/README.md` for channel layout, time calibration, and replication constraints.
- `DECISIONS.md` for the shared time-axis rule.
- `STYLE.md` for the required plot appearance.

# segmentation_diagnostic

## Method

- Load `data/off_to_on.tif` without changing the source file and verify its two-channel `ZCYX` layout.
- Select one timepoint reproducibly with random seed 2,151. The selected zero-based timepoint is 1,297, but the frame number is intentionally omitted from the figure because it is not part of the comparison.
- Build a stable rail reference as the pixelwise temporal median of 101 evenly spaced DNA-rail timepoints spanning the recording.
- Smooth the rail reference with a one-pixel Gaussian kernel, subtract a broad Gaussian background with sigma 12 pixels, and apply Otsu's automatic threshold.
- Remove connected detections smaller than 12 pixels, close one-pixel gaps, fill holes smaller than 12 pixels, and expand the resulting rail mask by two pixels.
- Define the local background as a band beginning four pixels and ending ten pixels outside the expanded rail mask.
- Apply the fixed DNA-derived mask directly to the paired motor channel because both channels in this TIFF share the same pixel coordinates.
- Calculate the descriptive on-rail excess as the mean motor intensity inside the rail mask minus the median motor intensity in the local background band.
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
- Local-background band: 4–10 pixels outside the expanded rail mask.
- Measurement: mean on-rail motor intensity minus median local motor background, in raw detector intensity units.
- Saturation diagnostic: fraction of rail-mask motor pixels equal to the 16-bit detector maximum of 65,535.
- Output: `parking/fluorescence_dynamics/plots/segmentation_diagnostic.pdf`.

## Statistics

- None; this output is descriptive.
- Descriptive summaries: the motor-intensity distributions in the rail mask and local background band, their reference lines, the background-subtracted on-rail excess, and the fraction of rail pixels at the detector maximum.
- No null hypothesis, alternative hypothesis, inferential threshold, model, or statistical test is used.
- Pixel values are spatially related measurements within one frame and are not treated as independent experimental replicates.

## Legends

- X axis: image x-coordinate in pixels for image panels, with labels hidden; raw motor intensity in arbitrary detector units for the distribution panel.
- Y axis: image y-coordinate in pixels for image panels, with labels hidden; probability density for the distribution panel.
- Color/value: grayscale is recorded or processed fluorescence intensity; dark red identifies the rail mask or its motor values; midnight blue identifies the local off-rail background band or its motor values.
- Grouping: one selected OFF-to-ON timepoint plus the fixed rail reference built from the same recording.
- Ordering/sorting: raw and processed rail diagnostics occupy the top row; motor projection and measurement diagnostics occupy the bottom row.
- Lines/markers/labels: solid contours outline spatial measurement regions; dashed vertical lines mark the median local background and mean rail-region motor intensity.
- Panels: raw DNA rails; processed rail reference; final rail mask; rail and local-background regions; raw motor channel; rail mask on motor; motor signal restricted to rails; motor-intensity comparison.

## Interpretation

- The raw and processed rail panels show whether denoising and broad-background subtraction preserve visible rail structures.
- The mask overlays show whether the DNA-derived region follows rails without absorbing large areas of background.
- The motor overlay and restricted-motor panel show exactly which motor pixels contribute to the proposed fluorescence measurement.
- Separation between the rail-region and local-background motor distributions indicates that the selected rail region contains motor signal beyond nearby off-rail fluorescence in this diagnostic frame.
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
