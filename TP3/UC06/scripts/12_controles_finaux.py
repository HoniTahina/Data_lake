from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pathlib import Path
import json

BASE = "hdfs://localhost:9000/retail-lake"

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-Controles-Finaux")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

rapport = {"tables": {}, "controles": {}}

try:
    chemins = {
        "silver_store": "silver/uc06_store",
        "silver_item": "silver/uc06_item",
        "silver_store_sales": "silver/uc06_store_sales",
        "gold_ventes_magasins": "gold/uc06_ventes_magasins",
        "gold_ventes_articles": "gold/uc06_ventes_articles",
        "gold_finance_magasins": "gold/uc06_finance_magasins",
        "gold_finance_articles": "gold/uc06_finance_articles"
    }

    print("===== INVENTAIRE PARQUET =====")

    for nom, chemin in chemins.items():
        df = spark.read.parquet(f"{BASE}/{chemin}")
        lignes = df.count()

        rapport["tables"][nom] = {
            "chemin": chemin,
            "lignes": lignes,
            "colonnes": len(df.columns)
        }

        print(f"{nom}: {lignes} lignes")

    # Comparer les deux agrégations financières
    dimensions = {
        "magasins": spark.read.parquet(
            f"{BASE}/gold/uc06_finance_magasins"
        ),
        "articles": spark.read.parquet(
            f"{BASE}/gold/uc06_finance_articles"
        )
    }

    colonnes = [
        "nombre_lignes",
        "quantite_totale",
        "total_ventes",
        "total_net",
        "total_benefice"
    ]

    totaux = {}

    for nom, df in dimensions.items():
        agg = df.agg(*[
            F.sum(F.col(c)).alias(c)
            for c in colonnes
        ]).first()

        totaux[nom] = {
            c: str(agg[c]) for c in colonnes
        }

        print(f"\n===== TOTAUX {nom.upper()} =====")
        for c in colonnes:
            print(c, ":", agg[c])

    rapport["controles"]["totaux"] = totaux

    # Tous les agrégats doivent être identiques
    coherence = (
        totaux["magasins"] == totaux["articles"]
    )

    lignes_ok = (
        int(totaux["magasins"]["nombre_lignes"])
        == rapport["tables"]["silver_store_sales"]["lignes"]
    )

    rapport["controles"][
        "totaux_magasins_articles_identiques"
    ] = coherence

    rapport["controles"][
        "conservation_lignes_ventes"
    ] = lignes_ok

    print("\n===== VERDICT =====")
    print("Totaux cohérents :", coherence)
    print("Lignes conservées :", lignes_ok)

    if not coherence or not lignes_ok:
        raise ValueError("Contrôles finaux échoués")

finally:
    spark.stop()

sortie = Path(
    "TP3/UC06/quality/rapport_final_qualite.json"
)
sortie.parent.mkdir(parents=True, exist_ok=True)

sortie.write_text(
    json.dumps(
        rapport, indent=2, ensure_ascii=False
    ),
    encoding="utf-8"
)

print("Rapport enregistré :", sortie)
print("===== UC06 : CONTROLES FINAUX OK =====")
