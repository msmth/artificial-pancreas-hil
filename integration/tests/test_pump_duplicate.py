import asyncio
from bleak import BleakClient, BleakScanner

PUMP_NAME = "Simulated Insulin Pump"

INSULIN_UUID = "12345678-1234-1234-1234-123456789004"
STATUS_UUID = "12345678-1234-1234-1234-123456789005"

COMMAND = "BOLUS:bletest001:0.10"

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

    async with BleakClient(device) as client:
        print("Connected:", client.is_connected)

        async def send_and_read(command):
            # Read current status, then send the command.
            previous = (await client.read_gatt_char(STATUS_UUID)).decode().strip()

            await client.write_gatt_char(
                INSULIN_UUID, command.encode(), response=True
            )

            # Wait briefly for the ESP32 to process the write.
            await asyncio.sleep(0.5)

            status = (await client.read_gatt_char(STATUS_UUID)).decode().strip()
            print("Previous:", previous)
            print("Response:", status)
            print()

        print("First command:")
        await send_and_read(COMMAND)

        print("Repeated command:")
        await send_and_read(COMMAND)

asyncio.run(main())