import threading
import time

from simglucose_runner.meal_manager import MealManager
from simglucose_runner.simulation import Simulation
from simglucose_runner.run_logger import RunLogger
from simglucose_runner.serial_bridge import SerialBridge


# ---------- Configuration ----------

SIMULATION_MINUTES = 150
REAL_TIME_PER_MINUTE = 60.0
CGM_SAMPLE_INTERVAL = 5

# Hardware connection
ENABLE_CGM = True
CGM_PORT = "COM14"
CGM_BAUDRATE = 115200

# Set True to save CSV files; False for test runs without logging.
LOG_RUNS = True


# ---------- Terminal Commands ----------

def command_listener(meals, state, stop_event):
    """Read terminal commands without blocking the simulation."""
    print("Commands: meal <grams>, status, stop")

    while not stop_event.is_set():
        try:
            command = input().strip()
        except (EOFError, KeyboardInterrupt):
            stop_event.set()
            break

        if not command:
            continue

        parts = command.split()
        action = parts[0].lower()

        if action == "meal":
            if len(parts) != 2:
                print("\nUsage: meal <carbohydrate grams>")
                continue

            try:
                carbs = float(parts[1])
                meals.add_meal(carbs)
                print(f"\nQueued meal: {carbs:g} g")
            except ValueError as exc:
                print(f"\nInvalid meal: {exc}")

        elif action == "status":
            current = state["current"]
            print(
                f"\nTime: {current['time_min']} min | "
                f"Glucose: {current['glucose_mg_dL']:.2f} mg/dL"
            )

        elif action == "stop":
            stop_event.set()
            break

        else:
            print("\nUnknown command. Use: meal <grams>, status, stop")


# ---------- Main Simulation ----------

def main():
    simulation = Simulation()
    meals = MealManager()

    logger = RunLogger() if LOG_RUNS else None
    bridge = None
    stop_event = threading.Event()

    state = {"current": simulation.get_state()}
    status = "completed"

    # Connect to the CGM, if enabled.
    if ENABLE_CGM:
        try:
            bridge = SerialBridge(
                port=CGM_PORT,
                baudrate=CGM_BAUDRATE,
            )
            time.sleep(2)
            print(f"CGM serial connection opened on {CGM_PORT}.")

        except Exception:
            if logger is not None:
                logger.finish(state["current"], "error")
            raise

    # Start listening for terminal commands.
    listener = threading.Thread(
        target=command_listener,
        args=(meals, state, stop_event),
        daemon=True,
    )
    listener.start()

    # Record the initial state if logging is enabled.
    if logger is not None:
        logger.log_step(state["current"])

    if logger is not None:
        print(f"Starting {logger.run_id}")
    else:
        print("Starting test run (logging disabled)")

    print(
        "CGM hardware mode."
        if bridge
        else "Simulation-only mode; no hardware connections."
    )
    print("Enter: meal 60, status, or stop")

    try:
        while (
            simulation.time_min < SIMULATION_MINUTES
            and not stop_event.is_set()
        ):
            # Retrieve a queued meal, if available.
            meal = meals.get_next_meal()

            if meal > 0:
                print(
                    f"\nApplying meal of {meal:g} g "
                    f"at simulation minute {simulation.time_min}"
                )

            # Advance the simulated patient by one minute.
            result = simulation.step(meal_carbs_g=meal)
            state["current"] = result

            # Log only when logging is enabled.
            if logger is not None:
                logger.log_step(
                    result,
                    meal_carbs_g=meal,
                    insulin_units=0.0,
                )

            # Send glucose to the CGM at the configured interval.
            if result["time_min"] % CGM_SAMPLE_INTERVAL == 0:
                glucose = result["glucose_mg_dL"]

                print(
                    f"[{result['time_min']:03d} min] "
                    f"Glucose: {glucose:.2f} mg/dL | "
                    f"Meal: {meal:g} g"
                )

                if bridge is not None:
                    bridge.send_glucose(glucose)

            time.sleep(REAL_TIME_PER_MINUTE)

    except KeyboardInterrupt:
        stop_event.set()
        status = "interrupted"

    except Exception:
        status = "error"
        raise

    finally:
        stop_event.set()

        if bridge is not None:
            bridge.close()

        if (
            simulation.time_min < SIMULATION_MINUTES
            and status == "completed"
        ):
            status = "stopped"

        if logger is not None:
            logger.finish(state["current"], status)

    print(
        f"Simulation ended at minute {simulation.time_min} "
        f"({status})."
    )


if __name__ == "__main__":
    main()