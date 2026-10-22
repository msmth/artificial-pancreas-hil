# SimGlucose to oref0 Profile Mapping

## Purpose

Document how synthetic SimGlucose patient parameters map to the
oref0 profile used in the attributed IDS hardware-in-the-loop testbed.

This is a research configuration for software experimentation, not a
clinically validated treatment profile.

## Parameter mapping

| oref0 field | Candidate source | Status |
|---|---|---|
| `carb_ratio` | SimGlucose `Quest.csv` CR | Source value available; mapping to verify |
| `sens` | SimGlucose `Quest.csv` CF | Units and mapping unverified |
| `current_basal` | SimGlucose basal reference | Candidate only; validation required |
| `basalprofile` | Explicit schedule derived from approved experiment settings | Not configured |
| `isfProfile` | Explicit sensitivity schedule | Not configured |
| `carb_ratios` | Explicit carbohydrate-ratio schedule | Not configured |
| `min_bg`, `max_bg` | Explicit experimental target range | Not configured |
| `bg_targets` | Explicit target schedule | Not configured |
| `dia` | Explicitly selected experimental assumption | Not configured |
| `max_iob` | Explicitly selected experimental constraint | Not configured |
| `max_basal` | Explicitly selected experimental constraint | Not configured |
| `timezone` | `Europe/London` | Configured |

## Known SimGlucose source values

For `adult#001`:

- Carbohydrate ratio (CR): 10
- Correction-factor source value (CF): 8.773107
- Total daily insulin (TDI): 50.416652 U
- Body weight: 102.32 kg
- Baseline glucose: 138.56 mg/dL
- `u2ss`: 1.238624
- Calculated basal reference: approximately 1.2674 U/hour

These are source values or calculations, not a validated oref0 profile.

## Implementation rules

1. Do not infer undocumented units.
2. Do not silently substitute oref0 defaults for unresolved settings.
3. Keep source parameters separate from experimental assumptions.
4. Do not generate a profile while required settings remain unresolved.
5. Validate the generated JSON structure before invoking oref0.
6. Treat oref0 output as a recommendation, not delivered insulin.
7. Only a separately validated pump simulator report may determine
   the insulin input supplied to SimGlucose.
8. Keep all pump interactions simulation-only.

## Outstanding questions

- Confirm the units and interpretation of SimGlucose CF.
- Establish a defensible mapping between SimGlucose and oref0 sensitivity.
- Determine how the SimGlucose insulin input represents delivered insulin.
- Specify and justify the experimental DIA, glucose targets, `max_iob`,
  and `max_basal` before configuration.
- Test the generated profile against the exact oref0 revision in use.