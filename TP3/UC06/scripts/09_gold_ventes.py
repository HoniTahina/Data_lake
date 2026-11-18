from pyspark.sql import SparkSession
from pyspark.sql import functions as F

BASE = "hdfs://localhost:9000/retail-lake"

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-Gold-Ventes")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    # 1. Lecture des tables Silver
    ventes = spark.read.parquet(
        f"{BASE}/silver/uc06_store_sales"
    )

    articles = spark.read.parquet(
        f"{BASE}/silver/uc06_item"
    )

    magasins = spark.read.parquet(
        f"{BASE}/silver/uc06_store"
    )

    # 2. Préparation des clés
    v = ventes.select(
        F.col("_c2").alias("article_id"),
        F.col("_c7").alias("magasin_id")
    )

    a = articles.select(
        F.col("_c0").cast("string").alias("article_id")
    )

    m = magasins.select(
        F.col("_c0").cast("string").alias("magasin_id")
    )

    # 3. Contrôles avant jointure
    total_source = v.count()

    if a.distinct().count() != a.count():
        raise ValueError("Identifiants articles non uniques")

    if m.distinct().count() != m.count():
        raise ValueError("Identifiants magasins non uniques")

    # 4. Jointure avec les dimensions
    enrichies = (
        v.join(a, "article_id", "inner")
         .join(m, "magasin_id", "inner")
    )

    total_jointure = enrichies.count()

    print("===== CONTROLE JOINTURE =====")
    print("Lignes source :", total_source)
    print("Lignes après jointure :", total_jointure)

    if total_jointure != total_source:
        raise ValueError(
            "La jointure ne conserve pas toutes les ventes"
        )

    # 5. Agrégation par magasin
    gold_magasins = (
        enrichies
        .groupBy("magasin_id")
        .agg(
            F.count("*").alias("nombre_lignes_ventes")
        )
    )

    # 6. Agrégation par article
    gold_articles = (
        enrichies
        .groupBy("article_id")
        .agg(
            F.count("*").alias("nombre_lignes_ventes")
        )
    )

    # 7. Contrôle des agrégations
    for nom, df in [
        ("magasins", gold_magasins),
        ("articles", gold_articles)
    ]:
        total_agrege = df.agg(
            F.sum("nombre_lignes_ventes")
        ).first()[0]

        print(f"\n===== GOLD {nom.upper()} =====")
        print("Nombre de groupes :", df.count())
        print("Somme des lignes :", total_agrege)

        if total_agrege != total_source:
            raise ValueError(
                f"Total incohérent pour {nom}"
            )

        df.orderBy(
            F.desc("nombre_lignes_ventes")
        ).show(10, truncate=False)

    # 8. Ecriture dans la zone Gold
    gold_magasins.write \
        .mode("errorifexists") \
        .option("compression", "snappy") \
        .parquet(f"{BASE}/gold/uc06_ventes_magasins")

    gold_articles.write \
        .mode("errorifexists") \
        .option("compression", "snappy") \
        .parquet(f"{BASE}/gold/uc06_ventes_articles")

    # 9. Relecture des résultats
    for nom, chemin in [
        ("magasins", "uc06_ventes_magasins"),
        ("articles", "uc06_ventes_articles")
    ]:
        controle = spark.read.parquet(
            f"{BASE}/gold/{chemin}"
        )

        total = controle.agg(
            F.sum("nombre_lignes_ventes")
        ).first()[0]

        if total != total_source:
            raise ValueError(
                f"Erreur de relecture Gold : {nom}"
            )

        print(f"Relecture Gold {nom} : OK")

    print("\n===== TRAITEMENT GOLD TERMINE =====")

finally:
    spark.stop()
