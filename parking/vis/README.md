# on_to_off_middle_frame

## Method

- Load `data/on_to_off.tif` without changing the source file.
- Count the stored frames and select the middle frame with integer division: `number of frames // 2`.
- Split the 512-pixel-wide frame at its centre column. The left half is the motor-protein view and the right half is the DNA-rail view of the same scene.
- Display the two halves side by side in grayscale.
- Set the black and white display limits separately for each half using its 1st and 99.8th pixel-intensity percentiles. This improves visibility but does not change the stored values.
- Do not denoise, subtract background, segment structures, align channels, average frames, or measure fluorescence.
- Write `plots/on_to_off.pdf`.

## Variables

- Data/input: `data/on_to_off.tif`, a 16-bit 512 x 512 time series with 2,000 stored frames.
- Selected observation: zero-based frame 1,000, the middle stored frame.
- Panel mapping: columns 0–255 are motor proteins; columns 256–511 are DNA rails.
- Signal shown: raw 16-bit fluorescence intensity.
- Display limits: 1st and 99.8th intensity percentiles, calculated separately for each panel.
- Output: `parking/vis/plots/on_to_off.pdf`.

## Statistics

- None; this output is descriptive.
- No null hypothesis, alternative hypothesis, statistical threshold, model, or test is used.
- The percentile limits control display contrast only and must not be interpreted as detection thresholds.

## Legends

- X axis: image x-coordinate in pixels; tick labels are hidden.
- Y axis: image y-coordinate in pixels; tick labels are hidden.
- Color/value: black indicates lower raw fluorescence intensity and white indicates higher raw fluorescence intensity within each panel's display range.
- Grouping: one middle frame split into its two simultaneously recorded views.
- Ordering/sorting: motor-protein view on the left; DNA-rail view on the right.
- Lines/markers/labels: no lines or markers; panel titles identify the recorded view.
- Panels: left, motor proteins; right, DNA rails.

## Interpretation

- Use this PDF to inspect the ON-to-OFF recording's middle frame and confirm that both views contain visible structures before analysis.
- Do not use this figure to infer a time trend, switching effect, motor rate, or statistical difference.

## Notes

- This is an exploration figure, not a quantitative result.
- The raw TIFF contains one recording and is not an independent replicate of any other recording.

## References

- `data/README.md` for the source-data inventory and recording constraints.

# on_to_off_video

## Method

- Load `data/on_to_off.tif` without changing the source file.
- Select 240 source frames evenly from the first through the last stored frame so that the full recording is represented.
- Split every selected frame at the centre column. Display the motor-protein view on the left and the DNA-rail view on the right.
- Read the elapsed time stored with each selected frame and subtract the first selected timestamp so that the video begins at zero.
- Hold the grayscale display limits fixed through the video. Calculate separate motor and rail limits from the 1st and 99.8th intensity percentiles across all selected frames.
- Encode the 240 selected frames at 12 frames per second, producing a 20-second MP4 without interpolating intermediate frames.
- Write `plots/on_to_off.mp4`.

## Variables

- Data/input: `data/on_to_off.tif`, a 16-bit 512 x 512 time series with 2,000 stored frames.
- Selected observations: 240 evenly spaced zero-based frame indices including the first and last frames.
- Panel mapping: columns 0–255 are motor proteins; columns 256–511 are DNA rails.
- Clock: actual per-frame `ElapsedTime-ms` metadata relative to the first selected frame, displayed as hours:minutes:seconds.
- Display limits: fixed 1st and 99.8th intensity percentiles calculated separately for motor and rail pixels across the selected frames.
- Playback: 12 output frames per second for 20 seconds.
- Output: `parking/vis/plots/on_to_off.mp4`.

## Statistics

- None; this output is descriptive.
- No null hypothesis, alternative hypothesis, statistical threshold, model, or test is used.
- Percentiles control display contrast only and are not detection thresholds.

## Legends

- X axis: image x-coordinate in pixels; tick labels are hidden.
- Y axis: image y-coordinate in pixels; tick labels are hidden.
- Color/value: black indicates lower raw fluorescence intensity and white indicates higher raw fluorescence intensity within each channel's fixed display range.
- Grouping: paired motor-protein and DNA-rail views from the same selected source frame.
- Ordering/sorting: selected frames remain in acquisition order from the beginning to the end of the recording.
- Lines/markers/labels: the bottom clock shows actual elapsed acquisition time; no lines or markers are drawn.
- Panels: motor proteins on the left; DNA rails on the right.

## Interpretation

- Use the video to inspect the entire ON-to-OFF recording rapidly while preserving its chronological order and actual elapsed-time labels.
- Because contrast is fixed within each channel, changes in displayed brightness over time are not caused by frame-by-frame rescaling.
- This accelerated overview does not itself quantify motor fluorescence, rail occupancy, or directed runs.

## Notes

- The 20-second playback is a heavily subsampled overview of approximately 76 minutes of acquisition time.
- Playback speed is not the experimental frame rate; the bottom clock reports experimental time.

## References

- `data/README.md` for source-data layout and timing metadata.
- `nanu_poster/dual_channel_display.py` for the shared two-panel display and clock formatting.

# off_to_on_video

## Method

- Load `data/off_to_on.tif` without changing the source file and verify its two-channel `ZCYX` layout.
- Treat the first stack dimension as ordered timepoints and select 240 timepoints evenly from the first through the last stored timepoint.
- Read channel 1 as motor proteins and channel 0 as DNA rails. Display motor proteins on the left and DNA rails on the right.
- Assign elapsed time as `timepoint index x 2.188 seconds`, following the project time-axis decision for this TIFF.
- Hold the grayscale display limits fixed through the video. Calculate separate motor and rail limits from the 1st and 99.8th intensity percentiles across all selected timepoints.
- Encode the 240 selected timepoints at 12 frames per second, producing a 20-second MP4 without interpolating intermediate frames.
- Write `plots/off_to_on.mp4`.

## Variables

- Data/input: `data/off_to_on.tif`, a 16-bit stack with 2,089 ordered timepoints, two channels, 392 rows, and 256 columns.
- Selected observations: 240 evenly spaced zero-based timepoint indices including the first and last timepoints.
- Panel mapping: channel 1 is motor proteins; channel 0 is DNA rails.
- Clock: zero-based timepoint index multiplied by the assumed 2.188-second interval, displayed as hours:minutes:seconds.
- Display limits: fixed 1st and 99.8th intensity percentiles calculated separately for motor and rail pixels across the selected timepoints.
- Playback: 12 output frames per second for 20 seconds.
- Output: `parking/vis/plots/off_to_on.mp4`.

## Statistics

- None; this output is descriptive.
- No null hypothesis, alternative hypothesis, statistical threshold, model, or test is used.
- Percentiles control display contrast only and are not detection thresholds.

## Legends

- X axis: image x-coordinate in pixels; tick labels are hidden.
- Y axis: image y-coordinate in pixels; tick labels are hidden.
- Color/value: black indicates lower raw fluorescence intensity and white indicates higher raw fluorescence intensity within each channel's fixed display range.
- Grouping: paired motor-protein and DNA-rail channels from the same selected source timepoint.
- Ordering/sorting: selected timepoints remain in stack order from the beginning to the end of the recording.
- Lines/markers/labels: the bottom clock shows assumed elapsed acquisition time; no lines or markers are drawn.
- Panels: motor proteins on the left; DNA rails on the right.

## Interpretation

- Use the video to inspect the entire OFF-to-ON recording rapidly while preserving its chronological order.
- Because contrast is fixed within each channel, changes in displayed brightness over time are not caused by frame-by-frame rescaling.
- This accelerated overview does not itself quantify motor fluorescence, rail occupancy, or directed runs.

## Notes

- The 20-second playback is a heavily subsampled overview of an assumed 76.14 minutes of acquisition time.
- The clock is inferred rather than measured because this TIFF contains no physical timing metadata.
- Playback speed is not the experimental frame rate; the bottom clock reports the assumed experimental time.

## References

- `data/README.md` and `DECISIONS.md` for the assumed time calibration.
- `nanu_poster/dual_channel_display.py` for the shared two-panel display and clock formatting.

# timing_consistency

## Method

- Load the per-frame `ElapsedTime-ms` values embedded in `data/on_to_off.tif` without loading or changing the image pixels.
- Subtract the first stored timestamp so that the first frame is time zero.
- Calculate the median interval between consecutive frames. The observed median is 2.188 seconds.
- Construct a constant-rate time axis as `frame index x 2.188 seconds`.
- Plot the constant-rate time against the actual elapsed time and add an identity line representing perfect agreement.
- Write `plots/timing_consistency.pdf`.

## Variables

- Data/input: the 2,000 per-frame elapsed timestamps in `data/on_to_off.tif`.
- Actual elapsed time: each embedded timestamp minus the first embedded timestamp, expressed in minutes.
- Assumed elapsed time: zero-based frame index multiplied by 2.188 seconds, expressed in minutes.
- Reference: `actual elapsed time = assumed elapsed time`.
- Output: `parking/vis/plots/timing_consistency.pdf`.

## Statistics

- None; this output is descriptive.
- Descriptive summary: the median of the 1,999 observed consecutive-frame intervals is 2.188 seconds.
- No null hypothesis, alternative hypothesis, statistical threshold, model, or test is used.

## Legends

- X axis: elapsed time in minutes if every frame were separated by the median 2.188-second interval.
- Y axis: actual elapsed time in minutes read from the TIFF metadata.
- Color/value: the dark-red line is recorded timing; the black dashed identity line is perfect constant timing.
- Grouping: all 2,000 frames from the single ON-to-OFF recording.
- Ordering/sorting: frames remain in acquisition order.
- Lines/markers/labels: distance above or below the identity line is accumulated timing error; the final marker is labelled with the end-of-recording difference.
- Panels: one timing-agreement panel.

## Interpretation

- Points on the identity line agree exactly with a constant 2.188-second frame interval.
- Points above the line mean that the real acquisition took longer than the constant-rate approximation; points below it mean that it took less time.
- The final difference shows how much timing error accumulates by the end of the recording.

## Notes

- This diagnostic evaluates the proposed constant-rate approximation; it does not measure fluorescence or switching behavior.
- The corresponding OFF-to-ON time axis will use the same assumed 2.188-second interval because that TIFF contains no physical timing metadata.

## References

- `data/README.md` for the source-data inventory and time-calibration rule.

# off_to_on_middle_frame

## Method

- Load `data/off_to_on.tif` without changing the source file.
- Verify that the TIFF is stored as a two-channel `ZCYX` ImageJ stack.
- Treat the first stack dimension as the ordered timepoint index because each `WalkAvg` label is repeated once for each of the two channels.
- Select the middle timepoint with integer division: `number of timepoints // 2`.
- Read channel 0 as the DNA-rail view and channel 1 as the motor-protein view, then display motor proteins on the left and DNA rails on the right.
- Set the black and white display limits separately for each channel using its 1st and 99.8th pixel-intensity percentiles.
- Do not denoise, subtract background, segment structures, align channels, average timepoints, or measure fluorescence.
- Write `plots/off_to_on.pdf`.

## Variables

- Data/input: `data/off_to_on.tif`, a 16-bit stack with shape 2,089 timepoints x 2 channels x 392 rows x 256 columns.
- Selected observation: zero-based timepoint 1,044, the middle stored timepoint.
- Channel mapping: channel 0 is DNA rails; channel 1 is motor proteins.
- Signal shown: raw 16-bit fluorescence intensity.
- Display limits: 1st and 99.8th intensity percentiles, calculated separately for each panel.
- Output: `parking/vis/plots/off_to_on.pdf`.

## Statistics

- None; this output is descriptive.
- No null hypothesis, alternative hypothesis, statistical threshold, model, or test is used.
- The percentile limits control display contrast only and must not be interpreted as detection thresholds.

## Legends

- X axis: image x-coordinate in pixels; tick labels are hidden.
- Y axis: image y-coordinate in pixels; tick labels are hidden.
- Color/value: black indicates lower raw fluorescence intensity and white indicates higher raw fluorescence intensity within each panel's display range.
- Grouping: the two recorded channels from one middle timepoint.
- Ordering/sorting: motor-protein channel on the left; DNA-rail channel on the right.
- Lines/markers/labels: no lines or markers; panel titles identify the recorded channel.
- Panels: left, motor proteins; right, DNA rails.

## Interpretation

- Use this PDF to inspect the OFF-to-ON recording's middle timepoint and confirm that both channels contain visible structures before analysis.
- Do not use this figure to infer a time trend, switching effect, motor rate, or statistical difference.

## Notes

- This is an exploration figure, not a quantitative result.
- The TIFF names the first stack dimension `Z`; its paired `WalkAvg` labels show that the dimension is the ordered timepoint index used for this visualization.
- The raw TIFF contains one recording and is not an independent replicate of the ON-to-OFF recording.

## References

- `data/README.md` for the source-data inventory and recording constraints.

# on_to_off_panels

## Method

- Load `data/on_to_off.tif` without changing the source file and select five evenly spaced frames spanning the full recording, including its first and last frames.
- Replace each selected single frame with the pixelwise mean of five consecutive raw frames centered on it when possible. Use the first five source frames for the first panel and the last five for the last panel. This suppresses frame-specific detector noise without averaging across distant experimental times.
- Split each five-frame average at its centre column. Treat the left half as motor fluorescence and the right half as DNA-rail fluorescence from the same scene and local time window.
- Apply a light Gaussian spatial smoothing with sigma 0.65 pixels separately to the motor and rail halves. Smoothing occurs after temporal averaging and never crosses the boundary between channels.
- Define one motor black point as the median of all five cleaned motor images plus three robust standard deviations, where robust standard deviation is `1.4826 × median absolute deviation`. Define one motor white point as their pooled 99.8th percentile. Apply these same two motor limits to every panel so the motor progression remains comparable through time and background noise maps to black.
- The raw rail channel photobleaches substantially. For the structural rail overlay only, calculate the same robust black point and 99.8th-percentile white point separately in each cleaned rail image. This prevents the progressively white, overexposed rail appearance in the old GIF while preserving each window's rail geometry.
- Apply the standard ImageJ/Fiji yellow monochrome lookup table to normalized motor intensity and the blue monochrome lookup table to normalized rail intensity. Add the two RGB layers and clip at white, so motor is yellow, rail is blue, and spatial overlap is white.
- Export each composite directly as a native-resolution lossless PNG without axes, labels, timestamps, borders, interpolation, cropping, segmentation, or spatial realignment.
- Write the five separate images to `plots/on_off_panels/`.

## Variables

- Data/input: `data/on_to_off.tif`, containing 2,000 raw 16-bit frames of 512 rows by 512 columns.
- Selected zero-based frames: 0, 499, 999, 1,499, and 1,999.
- Selected elapsed times: 0.00, 17.34, 37.03, 56.57, and 76.00 minutes from the embedded TIFF timestamps.
- Five-frame averaging windows: 0–4, 497–501, 997–1,001, 1,497–1,501, and 1,995–1,999.
- Panel mapping: columns 0–255 are motor proteins; columns 256–511 are DNA rails.
- Temporal filter: arithmetic mean of five adjacent raw frames.
- Spatial filter: Gaussian sigma 0.65 pixels, applied independently to each channel.
- Robust black-point rule: median plus `3 × 1.4826 × median absolute deviation`.
- Fixed motor display range after denoising: 695 to 1,923 detector units.
- Rail display ranges after denoising: 796–8,969; 624–5,038; 590–4,072; 577–3,208; and 568–2,737 detector units for the five selected windows, respectively.
- Lookup-table endpoints: motor yellow `[1, 1, 0]`; rail blue `[0, 0, 1]`; additive overlap is white `[1, 1, 1]`.
- Compute: up to 64 CPU workers read disjoint TIFF frame chunks; the averaged and smoothed channel images, source-window indices, display limits, and filter parameters are stored in `cache/on_to_off_panels.npz`.
- Outputs: `plots/on_off_panels/on_to_off_01.png` through `on_to_off_05.png`, each 256 pixels wide by 512 pixels high.

## Statistics

- None; these outputs are descriptive poster images.
- No null hypothesis, alternative hypothesis, statistical threshold, fitted model, or test is used.
- The temporal mean, Gaussian filter, and contrast rules are visualization transforms. They do not classify motor-positive pixels or measure rail or motor fluorescence.
- The fixed motor range is appropriate because it preserves motor brightness comparability through time. The per-window rail range is appropriate only because the rail is used here as a structural location guide and the user requested correction of its misleading progressive exposure.

## Legends

- X axis: image x-coordinate; no axis or tick labels are drawn.
- Y axis: image y-coordinate; no axis or tick labels are drawn.
- Color/value: yellow intensity is the normalized, locally averaged motor signal; blue intensity is the normalized, locally averaged DNA-rail signal; white indicates additive spatial overlap of strong motor and rail signals; black indicates signal at or below the robust channel background.
- Grouping: five paired motor-plus-rail composites from one ON-to-OFF recording.
- Ordering/sorting: filenames 01 through 05 follow acquisition order from 0 to approximately 76 minutes.
- Lines/markers/labels: none; each file contains only the composite microscopy image.
- Panels: five separate PNG files rather than one assembled multi-panel figure so each image can be placed independently on the poster.

## Interpretation

- The five images show the motor-channel progression across the full ON-to-OFF recording while keeping the rail in the intended blue and the motor in yellow.
- Temporal averaging and light spatial smoothing remove the isolated high-frequency yellow and blue speckle visible in the single-frame version, while the robust black points make empty regions black.
- The rail layer no longer changes progressively from blue to blown-out white because every selected rail window receives the same contrast rule.
- These are display composites for the poster. They should not be used to compare rail intensity between timepoints because the rail contrast is normalized separately in each window.

## Notes

- The TIFF metadata stores grayscale ImageJ lookup tables only; it does not preserve the poster's original pseudocolor assignment. Blue rails and yellow motors were inferred from the supplied poster reference and reproduced with ImageJ/Fiji's standard monochrome channel colors.
- The TIFF source remains unchanged. The PNGs are no longer single raw frames: each is a deliberately denoised display composite built from five nearby raw frames.
- Five-frame means can soften or slightly elongate a motor that moves during its local window. The short window was chosen to reduce noise without pooling distant stages of the experiment.
- Robust black clipping intentionally hides low-amplitude background fluctuations. Quantitative analyses continue to use the raw TIFF rather than these PNGs.
- The outputs use the full raw field of view and native pixel dimensions. Upscaling should be done only at poster placement time if required; it would not add image information.
- The existing middle-frame PDFs, timing plot, and overview MP4 files in this unit are unchanged.

## References

- ImageJ documentation for composite images, channel lookup tables, and channel merging: https://imagej.net/ij/docs/menus/image.html
- ImageJ color-processing documentation: https://imagej.github.io/imaging/color-image-processing
- `data/README.md` for source layout and timing metadata.
- `# on_to_off_video` in this README for the existing fixed-contrast full-recording overview.
