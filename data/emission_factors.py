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

    def get_factor(self, name, unit):
        factor_unit = f"kgCO2e/{unit}"
        if name in self.emission_factors and factor_unit in self.emission_factors[name]:
            return Decimal(self.emission_factors[name][factor_unit])
        return None


emission_factors = None


# Access the data through this function to avoid reading the file many times
def get_emission_factors():
    global emission_factors
    if emission_factors is None:
        emission_factors = EmissionFactors()
    return emission_factors
