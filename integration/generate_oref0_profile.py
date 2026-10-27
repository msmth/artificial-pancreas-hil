
import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
VALIDATOR = PROJECT_DIR / "integration" / "validate_patient_config.py"
CONFIG = PROJECT_DIR / "config" / "patients" / "adult_example.json"
OUTPUT = PROJECT_DIR / "data" / "profiles" / "adult_example.json"


def main():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        check=False,
    )

    if result.returncode != 0:
        print("\nProfile generation blocked: configuration is incomplete.")
        return result.returncode

    with CONFIG.open(encoding="utf-8") as file:
        config = json.load(file)

    source = config["simglucose_parameters"]
    profile_config = config["oref0_profile"]
    assumptions = config["experimental_assumptions"]

    # Do not guess how SimGlucose CF maps to oref0 sensitivity.
    if source.get("correction_factor_units") != "verified_mg_dL_per_U":
        print(
            "Profile generation blocked: correction-factor mapping "
            "has not been verified as mg/dL per U."
        )
        return 2

    basal_schedule = profile_config["basal_schedule"]
    sensitivity_schedule = profile_config["insulin_sensitivity_schedule"]
    target_schedule = profile_config["glucose_target_schedule"]

    basal_rate = source["basal_reference_U_per_hour"]

    if not isinstance(basal_schedule, list) or not basal_schedule:
        print("Profile generation blocked: basal schedule must be a non-empty list.")
        return 2

    if not isinstance(sensitivity_schedule, list) or not sensitivity_schedule:
        print("Profile generation blocked: sensitivity schedule must be a non-empty list.")
        return 2

    if not isinstance(target_schedule, list) or not target_schedule:
        print("Profile generation blocked: target schedule must be a non-empty list.")
        return 2

    dia = assumptions["dia_hours"]
    min_bg = assumptions["glucose_target_min_mg_dL"]
    max_bg = assumptions["glucose_target_max_mg_dL"]

    # Use the configured schedules directly; don't fabricate time-of-day values.
    carb_ratio = source["carbohydrate_ratio_g_per_U"]
    sensitivity = sensitivity_schedule[0]["sensitivity"]

    profile = {
        "name": config["patient_id"],
        "dia": dia,
        "timezone": profile_config["timezone"],
        "current_basal": basal_rate,
        "max_daily_basal": round(
            max(entry["rate"] for entry in basal_schedule), 3
        ),
        "basalprofile": basal_schedule,
        "sens": sensitivity,
        "isfProfile": {
            "units": "mg/dL",
            "sensitivities": sensitivity_schedule,
        },
        "carb_ratio": carb_ratio,
        "carb_ratios": {
            "units": "grams",
            "schedule": [
                {
                    **entry,
                    "ratio": entry["ratio"],
                    "r": entry["ratio"],
                }
                for entry in profile_config.get(
                    "carb_ratio_schedule",
                    [{"start": "00:00:00", "offset": 0, "ratio": carb_ratio,
                      "x": 0, "i": 0}],
                )
            ],
        },
        "min_bg": min_bg,
        "max_bg": max_bg,
        "bg_targets": {
            "units": "mg/dL",
            "targets": target_schedule,
        },
        "max_iob": assumptions["max_iob_U"],
        "max_basal": assumptions["max_basal_U_per_hour"],
        "min_5m_carbimpact": 8,
        "autosens_min": 0.7,
        "autosens_max": 1.2,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(profile, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(OUTPUT)

    print(f"Generated oref0 profile: {OUTPUT}")
    print("This confirms schema generation only, not clinical validity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
