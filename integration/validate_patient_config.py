import json
from pathlib import Path

CONFIG = (
    Path(__file__).resolve().parent.parent
    / "config" / "patients" / "adult_example.json"
)

REQUIRED_SOURCE_FIELDS = [
    "carbohydrate_ratio_g_per_U",
    "correction_factor_source_value",
    "correction_factor_units",
    "age_years",
    "total_daily_insulin_U",
    "body_weight_kg",
    "baseline_glucose_mg_dL",
    "u2ss",
    "basal_reference_U_per_min",
    "basal_reference_U_per_hour",
]

REQUIRED_PROFILE_FIELDS = [
    "basal_schedule",
    "insulin_sensitivity_schedule",
    "glucose_target_schedule",
    "dia_hours",
]

REQUIRED_ASSUMPTION_FIELDS = [
    "dia_hours",
    "glucose_target_min_mg_dL",
    "glucose_target_max_mg_dL",
    "max_iob_U",
    "max_basal_U_per_hour",
]


def main():
    with CONFIG.open(encoding="utf-8") as file:
        config = json.load(file)

    errors = []
    source = config.get("simglucose_parameters", {})
    profile = config.get("oref0_profile", {})
    assumptions = config.get("experimental_assumptions", {})

    for field in REQUIRED_SOURCE_FIELDS:
        if field not in source or source[field] is None:
            errors.append(f"Missing source parameter: {field}")

    for field in REQUIRED_PROFILE_FIELDS:
        value = profile.get(field)
        if value is None or value == []:
            errors.append(f"Profile needs configuration: {field}")

    if not profile.get("timezone"):
        errors.append("Profile needs configuration: timezone")

    if profile.get("status") != "configured":
        errors.append("Profile status is not 'configured'")

    for field in REQUIRED_ASSUMPTION_FIELDS:
        if assumptions.get(field) is None:
            errors.append(f"Experimental assumption needs review: {field}")

    if assumptions.get("status") != "reviewed":
        errors.append("Experimental assumptions are not marked 'reviewed'")

    if source.get("correction_factor_units") == "unverified":
        errors.append("Correction factor units and mapping remain unverified")

    print(f"Patient: {config.get('patient_id', 'unknown')}")
    print(f"Configuration: {CONFIG}")

    if errors:
        print("\nCONFIGURATION INCOMPLETE")
        for error in errors:
            print(f"- {error}")
        print("\nNo oref0 profile should be generated yet.")
        return 1

    print("\nCONFIGURATION COMPLETENESS CHECK PASSED")
    print("This does not establish clinical validity or safe operation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())