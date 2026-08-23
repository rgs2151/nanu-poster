# motor_run

**Research question:** Are the motors actually moving rather than merely binding or accumulating on the rails?

**Status:** Method planning only. No analysis script has been written, no recording has been processed, and no result has been calculated.

## Method

- Reuse the exact approved rail masks from the fluorescence-dynamics cache. The rail region remains the DNA-derived mask plus its fixed local expansion; motor brightness will not redefine it.
- Derive a one-pixel centreline from each approved rail mask only to create a distance coordinate and measure rail length. This is a geometric reduction of the accepted mask, not a new segmentation.
- Split the centreline at junctions so each usable piece is one unbranched path. A branched rail cannot be represented by one unambiguous distance axis.
- For every path and timepoint, average motor fluorescence across the narrow approved rail width at successive positions along the centreline. This converts the two-dimensional motor image into a one-dimensional intensity profile along that rail.
- Stack the profiles in time order to make a kymograph: horizontal position is distance along the rail and vertical position is time.
- Interpret a stationary bound motor as a vertical streak because its rail position stays constant while time passes. Interpret a moving motor as a diagonal streak because its rail position changes over time.
- Trace each sustained diagonal streak as one motor run. The streak slope gives that run's velocity, `velocity = change in rail position / elapsed time`; the sign gives its direction along the chosen rail coordinate.
- Use velocity only to verify and describe individual runs. The primary result will count runs because the question is how often productive motion occurs, including windows with zero runs.
- Assign each accepted run to the time window containing its start time. For a proposed 30-second window `w`, calculate `run rate(w) = accepted run starts in w / (total usable rail length × 0.5 minutes)`.
- Before any full-recording calculation, make a diagnostic showing representative rail paths, their kymographs, and the detected diagonal streaks overlaid. The full analysis will proceed only after that diagnostic is approved.
- If diagonal streaks cannot be separated reliably, stop rather than forcing the kymograph method. Direct two-dimensional blob detection and frame-to-frame linking would then be the alternative tracking method.

## Variables

- Planned data/input: `data/off_to_on.tif` and `data/on_to_off.tif`.
- Rail geometry: the exact approved cached rail mask plus its fixed expansion margin.
- Distance coordinate: cumulative distance along one unbranched centreline path.
- Time coordinate: exact embedded elapsed time for ON-to-OFF; timepoint index multiplied by 2.188 seconds for OFF-to-ON.
- Kymograph intensity: motor fluorescence averaged across the accepted rail width at one centreline position and one timepoint.
- Candidate run: one contiguous diagonal motor-intensity streak in a kymograph.
- Individual-run velocity: change in centreline distance divided by elapsed time. Velocity is a property of an accepted run, not the primary time-course y variable.
- Proposed time window: 30 seconds. This may be widened only if the diagnostic shows too few frames or runs per bin for a readable summary.
- Visible rail length: summed length of the usable unbranched centrelines, converted to micrometres after spatial calibration is confirmed.
- Primary measure: directed runs per micrometre of usable rail per minute.
- Pending run-acceptance choices: minimum consecutive frames, minimum displacement, allowable missed frames, minimum signal above local background, minimum and maximum plausible velocity, and treatment of junctions or overlapping streaks.
- Planned diagnostic: representative rail images, centreline paths, raw kymographs, and accepted-run overlays for both recordings.
- Planned final output: a one-row by two-column time course, with OFF-to-ON on the left and ON-to-OFF on the right.
- Current outputs: none.

## Statistics

- None selected or executed; the current unit is a measurement plan.
- Planned descriptive statistic: run rate in each time window, calculated as the number of accepted run starts divided by observed rail length and window duration.
- Null hypothesis: not yet selected.
- Alternative hypothesis: not yet selected.
- Run acceptance is a trajectory-classification rule, not a statistical-significance test. Its thresholds must be chosen from the diagnostic before counting the full recordings.
- Frames, rail segments, and runs are repeated observations within one field of view, not independent biological replicates.
- No p-value, confidence interval, null distribution, or population-level inference will be added without a separately approved statistical plan.

## Legends

- Kymograph x axis: distance along one unbranched rail path, in micrometres once spatial calibration is confirmed.
- Kymograph y axis: elapsed time, in seconds or minutes.
- Kymograph value: motor-fluorescence intensity sampled along that rail path.
- Kymograph lines: vertical streaks mean stationary bound signal; diagonal streaks mean displacement along the rail; the diagonal slope encodes velocity.
- Final-plot x axis: time after the first stored timepoint, in minutes.
- Final-plot y axis: directed motor runs per micrometre of usable rail per minute.
- Final-plot grouping: one panel per recording, using the established red family for OFF-to-ON and green family for ON-to-OFF.
- Final-plot ordering: OFF-to-ON left and ON-to-OFF right; timepoints remain in acquisition order.
- Final-plot panels: one row by two columns.

## Interpretation

- A kymograph is not a velocity plot and not an optical-flow field. It is an image of rail position versus time; velocity is encoded by the slope of a streak.
- A diagonal streak demonstrates that motor signal changed position along a rail. A vertical streak demonstrates binding or accumulation without measurable movement.
- Run rate answers how frequently directed movements occur. It is different from velocity, which answers how fast a motor moved after a run had already been detected.
- A rising OFF-to-ON run rate would indicate that activation produces more directed transport events.
- A low or falling ON-to-OFF run rate would indicate loss of directed transport.
- Rising rail fluorescence with no increase in run rate would mean that more motor signal binds or accumulates without a corresponding increase in productive motion.
- Velocity may be reported later as a secondary description, but velocity alone cannot represent a time window containing no runs.

## Notes

- Yes, this analysis requires tracking. Kymographs perform that tracking after collapsing a known rail path from two spatial dimensions into one distance dimension. Direct blob tracking instead links two-dimensional spot positions between frames.
- Kymographs are most useful when motion is constrained to a known, unbranched path. Junctions, crossing rails, overlapping motors, low frame rate, and diffuse fluorescence can make streaks ambiguous.
- The current project documentation does not contain a confirmed micrometres-per-pixel calibration. That calibration is required before reporting velocity or run rate in physical distance units.
- The proposed 30-second bins contain only about 14 timepoints at a 2.188-second interval. The diagnostic must establish whether that resolution is sufficient before fixing the final bin width.
- No code or analysis was run while creating this planning unit.

## References

- `parking/fluorescence_dynamics/README.md` for the approved rail segmentation and time-course measurement.
- `DECISIONS.md` for the fixed rail-region and time-axis definitions.
- `data/README.md` for channel mapping, timing assumptions, and the single-recording constraint.
- A motor-tracking or kymograph method reference will be added before execution.
