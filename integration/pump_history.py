
import json
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "pumphistory.json"
)


def record_bolus_delivery(amount_units, timestamp=None):
    """Record a bolus only after the simulated pump confirms delivery."""
    amount = float(amount_units)

    if amount <= 0:
        raise ValueError("Delivered bolus must be greater than zero.")

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must include a timezone.")

    event = {
        "timestamp": timestamp.isoformat(),
        "_type": "Bolus",
        "amount": amount,
        "duration": 0,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        history = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    else:
        history = []

    if not isinstance(history, list):
        raise ValueError("Pump history must be a JSON list.")

    history.insert(0, event)

    OUTPUT_FILE.write_text(
        json.dumps(history, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Recorded confirmed delivery: {amount:.3f} U")
