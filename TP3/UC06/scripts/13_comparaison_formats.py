import subprocess
import json
from pathlib import Path

BASE = "/retail-lake"

tables = {
    "store": {
        "raw": f"{BASE}/raw/nifi/store.dat",
        "silver": f"{BASE}/silver/uc06_store"
    },
    "item": {
        "raw": f"{BASE}/raw/tpcxbb/initial/item",
        "silver": f"{BASE}/silver/uc06_item"
    },
    "store_sales": {
        "raw": f"{BASE}/raw/tpcxbb/initial/store_sales",
        "silver": f"{BASE}/silver/uc06_store_sales"
    }
}

def taille_hdfs(chemin):
    resultat = subprocess.run(
        ["hdfs", "dfs", "-du", "-s", chemin],
        capture_output=True,
        text=True,
        check=True
    )

    # Première colonne : taille logique en octets
    return int(resultat.stdout.split()[0])

rapport = {}

print("===== COMPARAISON RAW / SILVER =====")

for nom, chemins in tables.items():
    raw = taille_hdfs(chemins["raw"])
    silver = taille_hdfs(chemins["silver"])

    reduction = (
        (raw - silver) / raw * 100
        if raw > 0 else None
    )

    rapport[nom] = {
        "raw_octets": raw,
        "silver_octets": silver,
        "reduction_pourcent": (
            round(reduction, 2)
            if reduction is not None else None
        )
    }

    print(f"\nTable : {nom}")
    print(f"RAW : {raw:,} octets")
    print(f"SILVER : {silver:,} octets")
    print(f"Réduction : {reduction:.2f}%")

sortie = Path(
    "TP3/UC06/quality/comparaison_formats.json"
)

sortie.parent.mkdir(parents=True, exist_ok=True)
sortie.write_text(
    json.dumps(rapport, indent=2),
    encoding="utf-8"
)

print("\nRapport enregistré :", sortie)
