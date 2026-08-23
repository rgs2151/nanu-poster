# Decisions

Use this file only for choices that must stay consistent across multiple analyses or outputs.

Do not put unit-specific file paths, temporary subsets, cache names, panel mappings, or one-off thresholds here. Put those details in the owning compact unit README.

## Time axes

- Decision: Set the first stored timepoint to zero. Use the embedded per-frame elapsed timestamps for the ON-to-OFF recording. For the OFF-to-ON recording, use `timepoint index x 2.188 seconds`, where 2.188 seconds is the median consecutive-frame interval in the ON-to-OFF recording.
- Why: The ON-to-OFF TIFF provides real timestamps, whereas the OFF-to-ON TIFF provides ordered timepoints but no physical time calibration. Applying the observed median interval supplies one explicit, consistent approximation for the uncalibrated stack.
- Use this when: Constructing time axes for visualizations and quantitative analyses of these two recordings.
- Do not use this for: Claiming that the OFF-to-ON acquisition rate was independently measured, or replacing the exact ON-to-OFF timestamps with a constant interval when exact timing matters.
- Notes: The assumed OFF-to-ON duration is approximately 76.14 minutes from its first to last timepoint.
