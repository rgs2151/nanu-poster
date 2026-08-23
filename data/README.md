# Data

This folder contains the source poster and the two raw fluorescence recordings used for the Nanu Poster analysis.

The large image files stay local and are ignored by git. Do not rename, move, overwrite, convert, or clean them without explicit approval.

## Structure

- `off_to_on.tif`: the single OFF-to-ON recording supplied for polymerase-driven activation.
- `on_to_off.tif`: the single ON-to-OFF recording supplied for nickase-driven deactivation.
- `[cleaned] poster_old.jpg`: the current poster reference. Its existing Results section is not evidence for the new analysis.
- Each recording contains a motor-protein view and a DNA-rail view of the same scene.
- `on_to_off.tif` stores both views side by side: columns 0–255 are motor proteins and columns 256–511 are DNA rails.
- `off_to_on.tif` stores two channels: channel 0 is DNA rails and channel 1 is motor proteins. Its first `ZCYX` dimension is treated as ordered timepoints because each `WalkAvg` label occurs once per channel.
- Spatial registration between the motor and rail views remains to be verified before measurement.
- `on_to_off.tif` contains a per-frame `ElapsedTime-ms` value. Subtract the first value to place its first stored frame at time zero; do not use the nominal 1 ms interval stored in the acquisition settings.
- `off_to_on.tif` contains no physical frame interval. Assign its first timepoint to zero and assume 2.188 seconds per timepoint, the median consecutive-frame interval measured in `on_to_off.tif`.
- The DNA-rail view will define the rail mask. That registered mask will then be applied to the motor-protein view; the motor channel must not be used to define the rail mask.
- There is one recording per transition. Frames, pixels, rail segments, and tracked runs are repeated observations within a recording, not independent experimental replicates.
- No missing frames, exclusions, or invalid time ranges have been declared yet.

## Inventory

| name | records | notes |
| --- | ---: | --- |
| `off_to_on.tif` | 2 channels x 2,089 timepoints | 16-bit ImageJ hyperstack; metadata reports 4,178 images. Channel 0 is DNA rails and channel 1 is motor proteins. Assume 2.188 seconds per timepoint. |
| `on_to_off.tif` | 2,000 frames at one stored position | 16-bit, 512 x 512 Micro-Manager TIFF. The motor view is the left 256 columns and the rail view is the right 256 columns. Use its per-frame elapsed-time metadata. |
| `[cleaned] poster_old.jpg` | 1 poster image | 19,860 x 28,080 pixels at 600 dpi; reference only. |
