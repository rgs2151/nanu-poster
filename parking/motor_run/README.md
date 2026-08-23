# motor_run

**Research question:** Are the motors actually moving rather than merely binding or accumulating on the rails?

## Method

- Analyze only motor fluorescence inside the fixed rail region approved in the fluorescence-dynamics analysis. The rail region remains the DNA-derived mask plus its two-pixel expansion; motor brightness cannot create or enlarge a rail.
- Label each connected rail structure, reduce it to a one-pixel skeleton, and retain the longest connected path through that skeleton. This gives each usable rail structure one unbranched position coordinate without segmenting the DNA channel again.
- Discard centreline paths shorter than 12 pixels. Retain 11 paths containing 627 sampled positions in OFF-to-ON and seven paths containing 390 sampled positions in ON-to-OFF.
- At each centreline position and timepoint, average motor intensity within a two-pixel-radius disk, restricted to pixels belonging to that same accepted rail structure. Stack these one-dimensional profiles through time to form one position-versus-time kymograph per path.
- Smooth each profile along rail position with sigma 0.8 pixels, subtract a broad positional background with sigma 4 pixels, and convert the remaining profile to a robust z score using its median and median absolute deviation.
- In every kymograph row, detect local peaks at least 3 robust standard deviations above the row median, with prominence at least 1 and separation at least two pixels. Keep at most the 12 strongest peaks per path and frame.
- Link peaks between consecutive frames with one missed frame allowed and a maximum positional step of eight pixels per elapsed frame. Perform linking independently within each unbranched rail path, so a trajectory can never jump between rail structures.
- Accept a linked trajectory as one directed movement only when it contains at least six observed positions, lasts at least six seconds, moves at least three pixels from start to end, has absolute fitted speed from 0.05 to 5 pixels per second, has linear-fit `R² >= 0.65`, and has directionality at least 0.65. Directionality is absolute start-to-end displacement divided by total stepwise travel; either travel direction counts.
- Assign each accepted movement to the one-minute bin containing its start time. Divide the count in a partial final bin by that bin's observed duration, then apply a centered five-minute average for display.
- Plot OFF-to-ON on the left and ON-to-OFF on the right in `plots/motor_run.pdf`. Cache the rail paths, raw and processed kymographs, all candidate trajectories, every acceptance metric, accepted start times, one-minute counts, and displayed averages.

## Variables

- Data/input: `data/off_to_on.tif` and `data/on_to_off.tif`.
- Rail geometry: the exact cached masks from `parking/fluorescence_dynamics/cache/fluorescence_dynamics.npz`; 7,918 accepted rail pixels in OFF-to-ON and 6,347 in ON-to-OFF.
- Mask provenance: source-cache SHA-256 `89b6389ddca4fdd9682acf67f91699163d1db31c2bd9475ef483ac1c4ce1bceb`; each reused rail-mask hash is also stored in this unit's cache.
- Usable paths: one longest path per connected rail structure after the 12-pixel minimum; 11 paths and 627 positions in OFF-to-ON, seven paths and 390 positions in ON-to-OFF.
- Kymograph x coordinate: sequential pixel position along one rail path. Physical distance is not reported because no micrometres-per-pixel calibration is available.
- Kymograph y coordinate: elapsed time. OFF-to-ON uses frame index multiplied by 2.188 seconds; ON-to-OFF uses its exact embedded elapsed timestamps.
- Candidate trajectory: a sequence of linked kymograph peaks on one path.
- Directed movement: a candidate trajectory passing all observation-count, duration, displacement, speed, linearity, and directionality rules.
- Final measure: accepted on-rail movement starts per minute.
- Display smoothing: centered five-minute average of the one-minute event rate; available bins are used at recording edges.
- Compute: 64 CPU workers read disjoint TIFF chunks. GPU acceleration is not used because TIFF decoding and sparse on-rail projection, rather than dense numerical kernels, dominate this calculation.
- Cache: `cache/motor_run.npz`, 13.5 MB, containing all geometry, kymographs, candidate trajectories, acceptance metrics, counts, parameters, and provenance hashes.
- Output: `plots/motor_run.pdf`.

## Statistics

- None; this output is descriptive.
- Descriptive summaries: accepted movement count, movement-start rate in each one-minute bin, and its centered five-minute average.
- Null hypothesis: not tested.
- Alternative hypothesis: not tested.
- Movement decision rule: a candidate must satisfy all six fixed trajectory criteria stated in the Method. These are signal- and trajectory-classification rules, not statistical-significance thresholds.
- Why this measure is appropriate: a bound but stationary motor remains at one rail position, whereas directed movement changes position through time. Counting accepted diagonal trajectories therefore answers whether on-rail motor signal moves without requiring an unavailable physical-distance calibration.
- Frames, trajectories, and rails are repeated observations within one field of view. The two recordings are not biological replicates, so no confidence interval, p-value, or population-level inference is reported.

## Legends

- X axis: time after the first stored timepoint in minutes.
- Y axis: `On-rail movements per minute`, meaning the number of accepted directed trajectories beginning per minute across all analyzed paths in that recording.
- Color/value: dark red (`#991B1B`) identifies OFF-to-ON and dark green (`#166534`) identifies ON-to-OFF.
- Grouping: one panel per recording.
- Ordering/sorting: one-minute bins remain in acquisition order.
- Lines/markers/labels: one solid line shows the centered five-minute average and is labeled `5-minute average`. Raw one-minute counts, markers, confidence bands, and significance annotations are omitted.
- Panels: one row by two columns; OFF-to-ON is left and ON-to-OFF is right. The y axis is shared from 0 to 1 movement per minute.

## Interpretation

- OFF-to-ON contains 10 accepted directed movements, equivalent to 0.131 movements per minute over the recording. No accepted movement begins in its first 18 minutes; subsequent movements occur in several separated bursts.
- ON-to-OFF contains two accepted directed movements, equivalent to 0.026 movements per minute, appearing as isolated events near 20 and 45 minutes.
- The observed movement frequency is fivefold higher in OFF-to-ON than ON-to-OFF within these two recordings.
- This result supports the interpretation that the accumulating OFF-to-ON rail fluorescence includes directed transport rather than only stationary binding. It does not imply that every fluorescence increase represents movement.
- Because there is one recording per transition, this is a descriptive difference between these fields of view, not evidence of population-level reproducibility.

## Notes

- The source fluorescence-dynamics cache remains unchanged. The motor-run cache is reused whenever present, so plot-only changes do not reread either TIFF or redetect trajectories.
- Both movement directions along a rail are counted. The arbitrary start-to-end orientation of a skeleton path therefore cannot change the event total.
- Skeletonization supplies only a position coordinate. Intensity sampling remains inside the full approved rail region, including its two-pixel margin.
- Branches are excluded from a path's one-dimensional coordinate by retaining one longest path per connected structure. Motion confined to an omitted side branch is not counted, so event totals are conservative with respect to branched structures.
- The six-observation minimum was fixed after the diagnostic audit showed that four-observation candidates were dominated by chance peak jumps. The cached candidate table retains rejected tracks and every decision metric for later sensitivity analysis.
- Saturation, overlapping motors, diffuse fluorescence, path crossings, and the approximately 2.2-second sampling interval can merge or hide trajectories. Accordingly, the accepted totals are detectable movement events, not counts of individual motor molecules.

## References

- Mangeol, P., Prevo, B., & Peterman, E. J. G. (2016). KymographClear and KymographDirect: two tools for the automated quantitative analysis of molecular and cellular dynamics using kymographs. *Molecular Biology of the Cell*, 27(12), 1948–1957. https://doi.org/10.1091/mbc.E15-06-0404
- Kushwaha, V. S., et al. (2020). The crowding dynamics of the motor protein kinesin-II. *PLOS ONE*, 15(2), e0228930. https://doi.org/10.1371/journal.pone.0228930
- `parking/fluorescence_dynamics/README.md` for the accepted segmentation geometry.
- `DECISIONS.md` for the fixed rail-region and time-axis definitions.
- `data/README.md` for channel mapping and the single-recording constraint.
- `STYLE.md` for plot appearance.

# motor_run_diagnostic

## Method

- Load the exact cached rail mask, rail reference, centreline paths, processed kymographs, and accepted trajectories used by `motor_run`; do not re-segment, reread the TIFFs, or rerun detection.
- For each recording, choose the rail path containing the largest number of accepted movements across the full recording.
- Show the DNA-rail reference with the accepted rail boundary, all analyzed paths in white, and the selected diagnostic path in black.
- Select one quiet one-minute endpoint window with the fewest accepted movements and one one-minute window containing an accepted movement. Selection uses only the cached event-start times on the displayed path.
- Display the processed position-versus-time kymograph for both windows and overlay only the accepted trajectory portions in the recording color.
- Write the two-row by three-column diagnostic to `plots/motor_run_diagnostic.pdf`.

## Variables

- Data/input: `parking/fluorescence_dynamics/cache/fluorescence_dynamics.npz` and `cache/motor_run.npz`.
- OFF-to-ON selected path: path 0, containing five accepted movements across the full recording.
- ON-to-OFF selected path: path 0, containing one accepted movement across the full recording.
- Diagnostic window duration: one minute.
- Stationary examples: the first minute of each recording, containing no accepted movement on either displayed path.
- Movement examples: a window around 23 minutes in OFF-to-ON and a window around 45 minutes in ON-to-OFF, each containing one accepted trajectory on the displayed path.
- Kymograph value: robust positional motor-intensity z score after narrow smoothing and broad positional-background removal.
- Output: `plots/motor_run_diagnostic.pdf`.

## Statistics

- None; this output is a measurement diagnostic.
- Descriptive summaries: total accepted movements on the selected path and accepted movement overlays within the displayed one-minute windows.
- Null hypothesis: not tested.
- Alternative hypothesis: not tested.
- Decision rule: only trajectories already passing every fixed `motor_run` acceptance rule are overlaid.
- Why this diagnostic is appropriate: it shows the spatial rail geometry, stationary vertical signal, and accepted position-changing signal in the same representation used for the final count.

## Legends

- X axis: sequential position along the selected rail path in pixels for each kymograph; image coordinates are hidden in the rail-reference panels.
- Y axis: elapsed time in minutes for each kymograph; image coordinates are hidden in the rail-reference panels.
- Color/value: grayscale shows the processed kymograph; red trajectories identify accepted OFF-to-ON movements and green trajectories identify accepted ON-to-OFF movements.
- Grouping: OFF-to-ON occupies the top row and ON-to-OFF the bottom row.
- Ordering/sorting: each row shows rail geometry, a stationary example, and a movement example from left to right.
- Lines/markers/labels: white lines show every analyzed centreline, black identifies the selected path, and the colored line over a kymograph is the accepted peak trajectory. Panel subtitles report accepted movement counts.
- Panels: two rows by three columns.

## Interpretation

- The path overlays confirm that motor signal is sampled only from the approved DNA-defined rail geometry.
- The stationary examples contain persistent near-vertical kymograph features but no accepted displacement trajectory.
- The movement examples show the position-changing trajectory portions that contribute event starts to the final time course.
- The diagnostic establishes traceability from rail geometry to accepted movement. It does not test the difference between recordings.

## Notes

- Movement windows are selected to expose the measurement logic, not to estimate typical event frequency. The complete recording, including every zero-event minute, enters `motor_run.pdf`.
- A one-minute window is used because accepted movements last seconds; a five-minute diagnostic window compressed their slopes and obscured the distinction from stationary signal.
- Rejected candidate tracks are deliberately not overlaid, but remain available in the cache with their rejection metrics.

## References

- Mangeol, P., Prevo, B., & Peterman, E. J. G. (2016). KymographClear and KymographDirect: two tools for the automated quantitative analysis of molecular and cellular dynamics using kymographs. *Molecular Biology of the Cell*, 27(12), 1948–1957. https://doi.org/10.1091/mbc.E15-06-0404
- `# motor_run` in this README for the complete trajectory-detection rules and result.
- `parking/fluorescence_dynamics/README.md` for the accepted rail-mask geometry.
