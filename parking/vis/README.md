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
