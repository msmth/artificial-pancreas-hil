
import csv
from datetime import datetime
from pathlib import Path


class RunLogger:
    """Save simulation data and run metadata to CSV files."""

    def __init__(self, logs_folder="logs"):
        self.logs_folder = Path(logs_folder)
        self.logs_folder.mkdir(parents=True, exist_ok=True)

        existing_runs = list(
            self.logs_folder.glob("run_*_data.csv")
        )
        run_numbers = []

        for path in existing_runs:
            try:
                run_numbers.append(
                    int(path.name.split("_")[1])
                )
            except (ValueError, IndexError):
                pass

        self.run_number = max(run_numbers, default=0) + 1
        self.run_id = f"run_{self.run_number:03d}"
        self.start_time = datetime.now().astimezone()

        self.data_path = (
            self.logs_folder / f"{self.run_id}_data.csv"
        )
        self.summary_path = (
            self.logs_folder / "run_summary.csv"
        )

        self.data_file = self.data_path.open(
            "w", newline="", encoding="utf-8"
        )
        self.writer = csv.writer(self.data_file)
        self.writer.writerow([
            "run_id",
            "timestamp",
            "simulation_minute",
            "glucose_mg_dL",
            "meal_carbs_g",
            "insulin_units",
        ])

        self.data_file.flush()

    def log_step(self, state, meal_carbs_g=0.0,
                 insulin_units=0.0):
        timestamp = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )

        self.writer.writerow([
            self.run_id,
            timestamp,
            state["time_min"],
            state["glucose_mg_dL"],
            meal_carbs_g,
            insulin_units,
        ])
        self.data_file.flush()

    def finish(self, final_state, status):
        end_time = datetime.now().astimezone()
        self.data_file.close()

        summary_exists = self.summary_path.exists()

        with self.summary_path.open(
            "a", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)

            if not summary_exists or self.summary_path.stat().st_size == 0:
                writer.writerow([
                    "run_id",
                    "start_datetime",
                    "end_datetime",
                    "duration_simulation_min",
                    "final_glucose_mg_dL",
                    "status",
                    "data_file",
                ])

            writer.writerow([
                self.run_id,
                self.start_time.isoformat(timespec="seconds"),
                end_time.isoformat(timespec="seconds"),
                final_state["time_min"],
                final_state["glucose_mg_dL"],
                status,
                self.data_path.name,
            ])

        print(f"Run data saved: {self.data_path}")
        print(f"Run summary saved: {self.summary_path}")
