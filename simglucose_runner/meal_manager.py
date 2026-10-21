from queue import Queue, Empty

class MealManager:
    # Queue meal events for the simulation

    def __init__(self):
        self._meals = Queue()

    def add_meal(self, carbs_g):
        # Queue a meal amount in grams of carbohydrate
        carbs_g = float(carbs_g)

        if not 0 < carbs_g <= 300:
            raise ValueError("Meal must be greater than 0 and at most 300g")

        self._meals.put(carbs_g)

    def get_next_meal(self):
        # Return the next queued meal, or zero if none is waiting
        try: 
            return self._meals.get_nowait()
        except Empty:
            return 0.0