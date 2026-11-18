from pyspark.sql import SparkSession
from pyspark.sql import functions as F

BASE = "hdfs://localhost:9000/retail-lake"

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-Gold-Indicateurs")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    # 1. Charger les ventes Silver
    ventes = spark.read.parquet(
        f"{BASE}/silver/uc06_store_sales"
    )

    # 2. Typage des indicateurs
    df = ventes.select(
        F.col("_c2").alias("article_id"),
        F.col("_c7").alias("magasin_id"),
        F.expr(
            "try_cast(_c10 as bigint)"
        ).alias("quantite"),
        F.expr(
            "try_cast(_c13 as decimal(18,2))"
        ).alias("prix_unitaire"),
        F.expr(
            "try_cast(_c15 as decimal(18,2))"
        ).alias("montant_ventes"),
        F.expr(
            "try_cast(_c20 as decimal(18,2))"
        ).alias("montant_net"),
        F.expr(
            "try_cast(_c22 as decimal(18,2))"
        ).alias("benefice")
    )

    # 3. Contrôles avant les agrégations
    total_source = df.count()

    invalides = df.filter(
        F.col("article_id").isNull()
        | F.col("magasin_id").isNull()
        | F.col("quantite").isNull()
        | (F.col("quantite") <= 0)
        | F.col("prix_unitaire").isNull()
        | F.col("montant_ventes").isNull()
        | F.col("montant_net").isNull()
        | F.col("benefice").isNull()
    ).count()

    ecarts = df.filter(
        F.abs(
            F.col("quantite")
            * F.col("prix_unitaire")
            - F.col("montant_ventes")
        ) > F.lit(0.01)
    ).count()

    print("===== CONTROLES =====")
    print("Lignes sources :", total_source)
    print("Lignes invalides :", invalides)
    print("Ecarts de montant :", ecarts)

    if invalides or ecarts:
        raise ValueError(
            "Contrôles qualité non satisfaits"
        )

    # 4. Construire les agrégations
    def agreger(colonne):
        return (
            df.groupBy(colonne)
            .agg(
                F.count("*").alias("nombre_lignes"),
                F.sum("quantite").alias(
                    "quantite_totale"
                ),
                F.sum("montant_ventes").alias(
                    "total_ventes"
                ),
                F.sum("montant_net").alias(
                    "total_net"
                ),
                F.sum("benefice").alias(
                    "total_benefice"
                )
            )
        )

    gold_magasins = agreger("magasin_id")
    gold_articles = agreger("article_id")

    # 5. Contrôle de conservation des lignes
    for nom, resultat in [
        ("MAGASINS", gold_magasins),
        ("ARTICLES", gold_articles)
    ]:
        somme = resultat.agg(
            F.sum("nombre_lignes")
        ).first()[0]

        print(f"\n===== GOLD {nom} =====")
        print("Nombre de groupes :", resultat.count())
        print("Somme des lignes :", somme)

        if somme != total_source:
            raise ValueError(
                f"Agrégation incohérente : {nom}"
            )

        resultat.orderBy(
            F.desc("total_ventes")
        ).show(10, truncate=False)

    # 6. Écriture Parquet sans écrasement
    sorties = [
        (
            gold_magasins,
            f"{BASE}/gold/uc06_finance_magasins"
        ),
        (
            gold_articles,
            f"{BASE}/gold/uc06_finance_articles"
        )
    ]

    for resultat, destination in sorties:
        resultat.write \
            .mode("errorifexists") \
            .option("compression", "snappy") \
            .parquet(destination)

        controle = spark.read.parquet(destination)

        lignes = controle.agg(
            F.sum("nombre_lignes")
        ).first()[0]

        if lignes != total_source:
            raise ValueError(
                "Relecture Parquet incohérente"
            )

        print("Parquet vérifié :", destination)

    print("\n===== GOLD FINANCIER TERMINE =====")

finally:
    spark.stop()
