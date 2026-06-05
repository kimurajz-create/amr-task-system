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
- marker geometry specifications
- marker bindings
- selected-map design geometry
- selected-map selectable-point bindings
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
- selected-map point selection
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
- marker geometry maps keyed by `marker_id`
- selected-map asset path and design size
- selected-map points keyed by `point_id`
- selected-map config warnings
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
- `markers`
- `selected_map`
- `locations`
- `missions`

## SelectedMap Contract

`site/<profile>.json` may define a top-level `selected_map` block:

- `design_width_px`
- `design_height_px`
- `empty_state_text`
- `selectable_points`

Each `selectable_points[*]` record defines:

- `point_id`: unique runtime identifier
- `location_mir_name`: reference to `locations[*].mir_name`
- `marker_id`: optional explicit marker reference
- `label`: optional UI override
- `x_px`, `y_px`, `width_px`, `height_px`: clickable geometry in selected-map design space
- `order`: optional explicit ordering key
- `visible`: optional flag, defaults to visible

`build_site_runtime_maps()` now exposes these selected-map outputs:

- `selected_map_asset_path`
- `selected_map_design_size`
- `selected_map_empty_state_text`
- `selected_map_points`
- `selected_map_points_by_id`
- `selected_map_location_names`
- `selected_map_config_warnings`

Runtime builder rules:

- invalid or unresolved selected-map points are skipped with warnings instead of crashing
- `selected_label` falls back to the referenced location display name
- `marker_id` falls back to the referenced location's `marker_id`
- hidden points (`visible: false`) are omitted from runtime point lists

That schema would make adding new sites safer and easier.
