import json
import os
from decimal import Decimal


class Multipliers:
    def __init__(self):
        module_dir = os.path.dirname(__file__)
        file_path = os.path.join(module_dir, "static/multipliers.json")
        with open(file_path, "r") as f:
            self.multipliers = json.load(f)

    def get_multiplier(self, name, unit):
        multiplier_unit = f"kgCO2e/{unit}"
        if name in self.multipliers and multiplier_unit in self.multipliers[name]:
            return Decimal(self.multipliers[name][multiplier_unit])
        return None


multipliers = None


# Access the data through this function to avoid reading the file many times
def get_multipliers():
    global multipliers
    if multipliers is None:
        multipliers = Multipliers()
    return multipliers
