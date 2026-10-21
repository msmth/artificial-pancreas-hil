
import asyncio
import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient, BleakScanner


# ---------- Configuration ----------

CGM_NAME = "Simulated Glucose Sensor"

GLUCOSE_CHARACTERISTIC_UUID = (
    "12345678-1234-1234-1234-123456789002"
)

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "glucose.json"
MAX_READINGS = 24


# Keep the newest readings first; retain up to 24 readings.
readings = deque(maxlen=MAX_READINGS)


# ---------- Save Glucose History ----------

def save_reading(glucose_value):
    """Record a reading and save the history in oref0 format."""
    now = datetime.now(timezone.utc)

    reading = {
        "date": int(now.timestamp() * 1000),
        "dateString": now.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "sgv": round(glucose_value),
        "device": "simulated-cgm",
        "type": "sgv",
        "glucose": round(glucose_value),
    }

    # Avoid saving two readings with the same timestamp.
    if readings and reading["date"] <= readings[0]["date"]:
        reading["date"] = readings[0]["date"] + 1

    readings.appendleft(reading)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(list(readings), file, indent=2)
        file.write("\n")


# ---------- Glucose Notification Handler ----------

def handle_glucose(_sender, data: bytearray):
    """Decode, validate and save CGM notifications."""
    received_at = datetime.now(timezone.utc).isoformat()

    try:
        glucose_text = data.decode("utf-8").strip()
        glucose_value = float(glucose_text)

        if not 20 <= glucose_value <= 600:
            print(
                f"[{received_at}] Warning: glucose value outside "
                f"test range: {glucose_value}"
            )
            return

    except (UnicodeDecodeError, ValueError):
        print(f"[{received_at}] Invalid glucose payload: {data!r}")
        return

    try:
        save_reading(glucose_value)
    except OSError as exc:
        print(f"[{received_at}] Could not save glucose history: {exc}")
        return

    print(
        f"[{received_at}] Glucose: {glucose_value:.2f} mg/dL "
        f"| Saved {len(readings)} reading(s)"
    )


# ---------- Main BLE Receiver ----------

async def main():
    print(f"Searching for {CGM_NAME}...")

    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: (
            d.name == CGM_NAME
            or ad.local_name == CGM_NAME
        ),
        timeout=15.0,
    )

    if device is None:
        print(
            "CGM not found. Check that it is powered on "
            "and advertising."
        )
        return

    print(f"Found CGM: {device.address}")

    async with BleakClient(device) as client:
        print("Connected to CGM.")

        await client.start_notify(
            GLUCOSE_CHARACTERISTIC_UUID,
            handle_glucose,
        )

        print(f"Saving glucose history to: {OUTPUT_FILE}")
        print("Receiving glucose notifications. Press Ctrl+C to stop.")

        try:
            while True:
                await asyncio.sleep(1)
        finally:
            await client.stop_notify(
                GLUCOSE_CHARACTERISTIC_UUID
            )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCGM receiver stopped.")
