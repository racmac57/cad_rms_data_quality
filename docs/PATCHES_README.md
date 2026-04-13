# Patches folder

The **`patches/`** folder holds **patch files** (diffs), not runnable scripts.

## What they are

- **`complete_backfill_simplified_geometry_fix.patch`** – Documents the change to append `TEMP_FC_3857` (feature class with geometry) to the online service instead of `CFSTABLE` (which can be a table with no geometry). This change is **already applied** in `scripts/complete_backfill_simplified.py`.
- **`publish_with_xy_coordinates_no_changes_needed.patch`** – Documents that no code changes were required for that script (verification comments only). It is for reference only.

## Do they stay here or go with the other scripts?

**Keep them in `patches/`.**

- Patch files are **not executed**. They are applied with `git apply` or used as documentation.
- The “other scripts” live in **`scripts/`** (and similar). Those are the actual Python/PowerShell files that run.
- Moving `.patch` files into `scripts/` would mix documentation/diffs with runnable code and could confuse deployment (e.g. `Deploy-ToRDP-Simple.ps1` copies everything under `scripts/` to RDP; patches are not needed on the server).

So: **leave the patch files in `patches/`**. The fixes they describe are already in the script sources under `scripts/`.
