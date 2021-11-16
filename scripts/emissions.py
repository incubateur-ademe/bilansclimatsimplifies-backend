import requests
import json


def ƒetch_emissions():
    r = requests.get(
        "https://data.ademe.fr/data-fair/api/v1/datasets/base-carbone(r)/lines?format=json&q_mode=simple&Type_Ligne_in=Poste&Type_de_l'%C3%A9l%C3%A9ment_in=Facteur%20d'%C3%A9mission&Statut_de_l'%C3%A9l%C3%A9ment_in=Valide%20g%C3%A9n%C3%A9rique%2CValide%20sp%C3%A9cifique&Type_poste_in=Combustion&sampling=neighbors&size=700"
    )
    body = r.json()
    results = body["results"]

    if body["total"] > len(results):
        raise Exception(
            f"There {body['total']} emissions but only {len(results)} fetched, please revise script/query to get all results"
        )
    return results


def import_results_from_file(filename):
    results = None
    with open(filename, "r", encoding="utf-8") as jsonfile:
        results = json.load(jsonfile)
    return results


def create_multipliers_file(results):
    multipliers = {}
    warning_zero = {}
    warning_duplicate = {}

    for emission in results:
        name = emission["Nom_base_français"]
        if name not in multipliers:
            multipliers[name] = {}
        unit = emission["Unité_français"]
        if unit not in multipliers[name]:
            multipliers[name][unit] = emission["Total_poste_non_décomposé"].replace(",", ".")
            if multipliers[name][unit] == 0:
                warning_zero[name] = warning_zero.get(name, 0) + 1
        else:
            if name not in warning_duplicate:
                warning_duplicate[name] = {}
            warning_duplicate[name][unit] = warning_duplicate[name].get(unit, 0) + 1

    with open("auto_multipliers.json", "w", encoding="utf8") as jsonfile:
        json.dump(multipliers, jsonfile, indent=2, ensure_ascii=False)

    print(warning_duplicate)
    print(warning_zero)
    print(f"Total zero multipliers: {len(warning_zero.keys())}")
    print(f"Total duplicates: {len(warning_duplicate.keys())}")
    return multipliers


def create_type_units_file(multipliers_dict):
    units = {}

    for name in multipliers_dict.keys():
        units[name] = [unit.split("kgCO2e/")[1] for unit in multipliers_dict[name].keys()]

    with open("auto_units.json", "w", encoding="utf-8") as jsonfile:
        json.dump(units, jsonfile, indent=2, ensure_ascii=False)


results = ƒetch_emissions()
multipliers = create_multipliers_file(results)
create_type_units_file(multipliers)
