# Les facteurs d'émission sont définies dans une fichier JSON plutôt qu'un classe de choix en Django
# car le client veut pouvoir les modifier, et cette méthode ne requiert pas une migration après.
import json
import os
from decimal import Decimal


class EmissionFactors:
    def __init__(self):
        module_dir = os.path.dirname(__file__)
        file_path = os.path.join(module_dir, "static/emission-factors.json")
        with open(file_path, "r") as f:
            self.emission_factors = json.load(f)

    def get_factor(self, type, unit, location):
        factor_unit = f"kgCO2e/{unit}"
        if type not in self.emission_factors:
            return None
        all_factors = self.emission_factors[type]["facteurs"]
        local_factors = None
        if location in all_factors:
            local_factors = all_factors[location]
        elif len(all_factors.keys()) == 1:
            default_location = list(all_factors.keys())[0]
            local_factors = all_factors[default_location]
        if local_factors is None:
            return None
        if factor_unit in local_factors:
            return Decimal(local_factors[factor_unit])
        return None

    def get_classification(self, type):
        if type not in self.emission_factors:
            return None
        return self.emission_factors[type]["classification"]


emission_factors = None


# Access the data through this function to avoid reading the file many times
def get_emission_factors():
    global emission_factors
    if emission_factors is None:
        emission_factors = EmissionFactors()
    return emission_factors
