# data/static/emission-factors.json is initially generated from this script.
# To update the file, run this script and copy the output, auto-emission-factors.json, to data/static/emission-factors.json.
# Be careful to keep changes that have been made to data/static/emission-factors.json if they're still relevant.

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
            f"There are {body['total']} emissions but only {len(results)} fetched, please revise script/query to get all results"
        )
    return results


def create_emission_factors_file(results):
    factors = {}
    duplicate_fe_by_unit = {}
    duplicate_count = 0

    for emission in results:
        name = emission["Nom_base_français"]
        unit = emission["Unité_français"]
        if name not in factors:
            factors[name] = {}

        # note if there is a duplicate unit for emission type
        if unit in factors[name]:
            if name not in duplicate_fe_by_unit:
                duplicate_fe_by_unit[name] = {}
            duplicate_fe_by_unit[name][unit] = duplicate_fe_by_unit[name].get(unit, 0) + 1
            duplicate_count += 1
        emission_factor = emission["Total_poste_non_décomposé"].replace(",", ".")

        # add to factors
        if unit not in factors[name]:
            factors[name][unit] = emission_factor

    with open("auto-emission-factors.json", "w", encoding="utf8") as jsonfile:
        json.dump(factors, jsonfile, indent=2, ensure_ascii=False)

    print(duplicate_fe_by_unit)
    print(f"Total duplicates: {duplicate_count}")
    return factors


results = ƒetch_emissions()
factors = create_emission_factors_file(results)
