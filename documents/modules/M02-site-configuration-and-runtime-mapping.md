# Site Configuration And Runtime Mapping

## Scope

Primary assets and code:

- `main.py`
- `site/company.json`
- `site/hospital.json`
- `app_settings.json`

## Responsibility

This module lets the same application run against different physical sites or demos by externalizing:

- map images and logo assets
- coordinate calibration
- location display names
- MiR location identifiers
- mission display names
- marker bindings
- room identifiers
- charging-station designation

## Main Behaviors

### Settings Resolution

The active site profile is resolved in this order:

1. `AMR_SITE_PROFILE` environment variable
2. `app_settings.json`
3. built-in default

### Site Config Loading

`load_site_config()` loads `site/<profile>.json`, merges missing fields with defaults, and falls back to `company` when the requested profile is unavailable or invalid.

### Runtime Map Building

`build_site_runtime_maps()` converts site configuration records into runtime dictionaries used by:

- UI combo boxes and labels
- task scheduler mission/location translation
- map marker highlighting
- room heartbeat mapping
- charging-station behavior

## Inputs

- selected site profile
- site JSON files
- default asset and calibration values

## Outputs

- `site_assets`
- `site_calibration`
- `USER_LOCATION_MAP` / `MIR_LOCATION_MAP` style mappings
- mission display-to-MiR mappings
- marker and room lookup tables
- required mission-code set for scheduler-related logic

## Boundaries

- This module defines site variability, not application workflow.
- It should provide mapping data, not directly manipulate widgets or DB state.
- It is configuration-driven but still partly coupled to hardcoded fallback dictionaries in `main.py`.

## Known Risks

- Hardcoded defaults in `main.py` can diverge from site JSON schema over time.
- Runtime map conventions are important but currently implicit.
- Validation for `site/*.json` appears lightweight, so malformed records may silently degrade behavior.

## Documentation Gap

A future schema document should define the expected shape for:

- `assets`
- `calibration`
- `locations`
- `missions`

That schema would make adding new sites safer and easier.
