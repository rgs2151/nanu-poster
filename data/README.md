# Data

This folder contains the source poster and the two raw fluorescence recordings used for the Nanu Poster analysis.

The large image files stay local and are ignored by git. Do not rename, move, overwrite, convert, or clean them without explicit approval.

## Structure

- `off_to_on.tif`: the single OFF-to-ON recording supplied for polymerase-driven activation.
- `on_to_off.tif`: the single ON-to-OFF recording supplied for nickase-driven deactivation.
- `[cleaned] poster_old.jpg`: the current poster reference. Its existing Results section is not evidence for the new analysis.
- Each recording contains a motor-protein view and a DNA-rail view of the same scene. The exact channel or split-screen layout, orientation, spatial offset, and time calibration must be verified before measurement.
- The DNA-rail view will define the rail mask. That registered mask will then be applied to the motor-protein view; the motor channel must not be used to define the rail mask.
- There is one recording per transition. Frames, pixels, rail segments, and tracked runs are repeated observations within a recording, not independent experimental replicates.
- No missing frames, exclusions, or invalid time ranges have been declared yet.

## Inventory

| name | records | notes |
| --- | ---: | --- |
| `off_to_on.tif` | 2 channels x 2,089 planes | 16-bit ImageJ hyperstack; metadata reports 4,178 images. Channel identities and time mapping remain to be verified. |
| `on_to_off.tif` | 2,000 frames at one stored position | 16-bit, 512 x 512 Micro-Manager TIFF. Per-frame elapsed-time metadata should be used rather than the nominal interval field. Split-view geometry remains to be verified. |
| `[cleaned] poster_old.jpg` | 1 poster image | 19,860 x 28,080 pixels at 600 dpi; reference only. |
