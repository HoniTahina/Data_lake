from pathlib import Path
from collections import Counter
import json

base = Path("retail_project/data")
tables = ["store", "store_sales", "item"]

resultats = {}

for table in tables:
    fichier = base / table / f"{table}.dat"

    largeurs = Counter()
    valeurs_vides = Counter()
    exemples = []
    nb_lignes = 0

    with fichier.open(
        "r", encoding="utf-8", errors="replace"
    ) as f:
        for ligne in f:
            if nb_lignes >= 1000:
                break

            champs = ligne.rstrip("\r\n").split("|")

            largeurs[len(champs)] += 1

            for i, valeur in enumerate(champs):
                if valeur == "":
                    valeurs_vides[f"_c{i}"] += 1

            if len(exemples) < 2:
                exemples.append(champs[:6])

            nb_lignes += 1

    resultats[table] = {
        "lignes_echantillon": nb_lignes,
        "largeurs_observees": dict(largeurs),
        "valeurs_vides": dict(valeurs_vides),
        "exemples_6_premiers_champs": exemples
    }

    print(f"\n===== {table.upper()} =====")
    print("Lignes analysées :", nb_lignes)
    print("Nombre de champs :", dict(largeurs))
    print("Champs vides :", dict(valeurs_vides))
    print("Exemples :", exemples)

sortie = Path("TP3/UC06/quality/audit_sources.json")
sortie.parent.mkdir(parents=True, exist_ok=True)

sortie.write_text(
    json.dumps(resultats, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("\nAudit sauvegardé :", sortie)
