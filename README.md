# Nanu Poster

Quantitative analysis of dual-channel TIRF recordings for enzymatic switching of motor-protein transport on dynamic DNA tracks.

## Setup

Create the environment from the repo root:

```bash
conda env create -f environment.yml
```

Activate it:

```bash
conda activate nanu-poster
```

Install the package in editable mode if needed:

```bash
python -m pip install -e .
```

## Running Units

Compact units live in `parking/` while they are being explored and in `figs/` after graduation.

Run one unit directly from the repo root:

```bash
python parking/<unit_name>/<unit_script>.py
```

Each unit owns its own `cache/` and `plots/` folders. Existing caches are reused by default. To recompute a unit, delete that unit's relevant cache or run the unit with an explicit recompute option when the script supports one.

## Data

Place organized analysis-ready data at:

```text
data/<real_data_file_or_folder>
```

See `data/README.md` for:

- data file names and locations
- dataset/table layout
- variable meanings
- alignment rules
- inventory of available records

## Project Docs

- `AGENTS.md`: working rules for Codex agents.
- `ORGANIZATION.md`: folder layout, compact-unit pattern, cache rules, and README template.
- `STYLE.md`: figure styling standards.
- `DECISIONS.md`: project-wide scientific or analytical decisions.
- `skills/`: repo-local Rudra workflow skills.
