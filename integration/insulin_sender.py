
import asyncio
import uuid
from datetime import datetime, timezone

from bleak import BleakClient, BleakScanner

from pump_history import record_bolus_delivery

PUMP_NAME = "Simulated Insulin Pump"

PUMP_SERVICE_UUID = "12345678-1234-1234-1234-123456789003"
INSULIN_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789004"
STATUS_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789005"

TEST_DOSE_UNITS = 0.10
ACK_TIMEOUT_SECONDS = 10


async def main():
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: (
            d.name == PUMP_NAME or ad.local_name == PUMP_NAME
        ),
        timeout=15,
    )

    if device is None:
        print("Pump not found.")
        return

    command_id = uuid.uuid4().hex[:12]
    expected_prefix = f"DELIVERED:{command_id}:"

    loop = asyncio.get_running_loop()
    ack_future = loop.create_future()

    def handle_status(_sender, data):
        status = data.decode("utf-8").strip()
        print(f"Pump status: {status}")

        if not ack_future.done():
            ack_future.set_result(status)

    async with BleakClient(device) as client:
        print(f"Connected to {PUMP_NAME}.")

        # Subscribe before writing so we don't miss the acknowledgement.
        await client.start_notify(
            STATUS_CHARACTERISTIC_UUID, handle_status
        )

        # Drain any status notification arriving before this test command.
        await asyncio.sleep(0.3)
        if ack_future.done():
            ack_future = loop.create_future()

        command = f"BOLUS:{command_id}:{TEST_DOSE_UNITS:.2f}"
        print(f"Sending simulated test command: {command}")

        # Never retry automatically: a timeout does not prove non-delivery.
        await client.write_gatt_char(
            INSULIN_CHARACTERISTIC_UUID,
            command.encode("utf-8"),
            response=True,
        )

        try:
            status = await asyncio.wait_for(
                ack_future, timeout=ACK_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            print(
                "No acknowledgement received. "
                "Do not retry automatically or record a delivery."
            )
            return
        finally:
            if client.is_connected:
                await client.stop_notify(STATUS_CHARACTERISTIC_UUID)

        if not status.startswith(expected_prefix):
            print(
                "Acknowledgement did not match this command. "
                "No history entry recorded."
            )
            return

        try:
            delivered_text = status[len(expected_prefix):]
            delivered_units = float(delivered_text)

            if delivered_units <= 0:
                raise ValueError("Non-positive delivery")

            # Record only after a matching acknowledgement.
            record_bolus_delivery(
                delivered_units,
                timestamp=datetime.now(timezone.utc),
            )
            print("Matching simulated delivery recorded.")
        except (ValueError, OSError) as exc:
            print(f"Could not record delivery: {exc}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPump sender stopped.")
