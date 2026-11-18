from pyspark.sql import SparkSession
from pyspark.sql import functions as F

SOURCE = "hdfs://localhost:9000/retail-lake/raw/nifi/store.dat"
DESTINATION = "hdfs://localhost:9000/retail-lake/silver/uc06_store"

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-Silver-Store")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    # 1. Lecture de la source brute
    df = (
        spark.read
        .option("header", "false")
        .option("sep", "|")
        .option("inferSchema", "false")
        .csv(SOURCE)
    )

    print("===== SOURCE =====")
    print("Lignes :", df.count())
    print("Colonnes :", len(df.columns))

    if len(df.columns) != 29:
        raise ValueError("Schéma inattendu : 29 colonnes attendues")

    # 2. Transformations explicites
    silver = (
        df
        .withColumn("_c0", F.col("_c0").cast("int"))
        .withColumn("_c2", F.to_date(F.col("_c2"), "yyyy-MM-dd"))
    )

    # 3. Contrôles qualité avant écriture
    total = silver.count()

    invalides = silver.filter(
        F.col("_c0").isNull() |
        F.col("_c2").isNull()
    ).count()

    doublons = total - silver.distinct().count()

    print("===== CONTROLES QUALITE =====")
    print("Total :", total)
    print("Identifiants ou dates invalides :", invalides)
    print("Doublons complets :", doublons)

    if invalides > 0 or doublons > 0:
        raise ValueError("Contrôles qualité non satisfaits")

    # 4. Vérification du schéma
    print("===== SCHEMA SILVER =====")
    silver.printSchema()

    # 5. Écriture Parquet, sans écrasement existant
    silver.write.mode("errorifexists").parquet(DESTINATION)

    # 6. Relecture du résultat
    verification = spark.read.parquet(DESTINATION)

    print("===== VERIFICATION PARQUET =====")
    print("Lignes relues :", verification.count())
    verification.select("_c0", "_c1", "_c2", "_c3").show(
        12, truncate=False
    )

finally:
    spark.stop()
