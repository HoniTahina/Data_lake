from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pathlib import Path
import json

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-Qualite")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

base = Path("/home/honi/retail-tp3-input")

sources = {
    "store": "store.dat",
    "store_sales": "store_sales_sample.dat",
    "item": "item_sample.dat"
}

rapport = {}

for nom, fichier in sources.items():
    print(f"\n===== TABLE : {nom.upper()} =====")

    df = (
        spark.read
        .option("header", "false")
        .option("sep", "|")
        .option("inferSchema", "false")
        .csv((base / fichier).as_uri())
    )

    total = df.count()
    distincts = df.distinct().count()
    doublons = total - distincts

    expressions = [
        F.sum(
            F.when(
                F.col(c).isNull() |
                (F.trim(F.col(c)) == ""),
                1
            ).otherwise(0)
        ).alias(c)
        for c in df.columns
    ]

    nulls = df.agg(*expressions).first().asDict()

    rapport[nom] = {
        "lignes": total,
        "colonnes": len(df.columns),
        "doublons_lignes_completes": doublons,
        "valeurs_manquantes": nulls,
        "echantillon": nom != "store"
    }

    print("Nombre de lignes :", total)
    print("Nombre de colonnes :", len(df.columns))
    print("Doublons complets :", doublons)

    print("Colonnes avec valeurs manquantes :")
    for colonne, nombre in nulls.items():
        if nombre:
            print(f"  {colonne}: {nombre}/{total}")

sortie = Path(
    "TP3/UC06/quality/audit_pyspark.json"
)

sortie.parent.mkdir(parents=True, exist_ok=True)
sortie.write_text(
    json.dumps(
        rapport,
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print("\nRapport enregistré :", sortie)

spark.stop()
