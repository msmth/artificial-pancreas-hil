from simglucose.patient.t1dpatient import T1DPatient, Action

class Simulation:
    # Manage one simglucose patient and its simulation clock

    def __init__(self, patient_name="adult#001"):
        self.patient = T1DPatient.withName(patient_name)
        self.time_min = 0

    def get_state(self):
        # Return the current simulation time and glucose
        return {
            "time_min": self.time_min,
            "glucose_mg_dL": float(self.patient.observation.Gsub),
        }

    def step(self, meal_carbs_g=0.0, insulin_units=0.0):
        # Advance the patient model by one simulated minute
        action = Action (
            insulin = insulin_units,
            CHO = meal_carbs_g,
        )

        self.patient.step(action)
        self.time_min += 1

        return self.get_state()