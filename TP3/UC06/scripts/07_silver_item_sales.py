from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-Silver-Item-Sales")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

tables = {
    "item": {
        "source": "hdfs://localhost:9000/retail-lake/raw/tpcxbb/initial/item/item.dat",
        "destination": "hdfs://localhost:9000/retail-lake/silver/uc06_item",
        "colonnes": 22
    },
    "store_sales": {
        "source": "hdfs://localhost:9000/retail-lake/raw/tpcxbb/initial/store_sales/store_sales.dat",
        "destination": "hdfs://localhost:9000/retail-lake/silver/uc06_store_sales",
        "colonnes": 23
    }
}

try:
    for nom, config in tables.items():
        print(f"\n===== TRAITEMENT : {nom.upper()} =====")

        # 1. Lecture HDFS
        df = (
            spark.read
            .option("header", "false")
            .option("sep", "|")
            .option("inferSchema", "false")
            .option("mode", "FAILFAST")
            .csv(config["source"])
        )

        if len(df.columns) != config["colonnes"]:
            raise ValueError(
                f"{nom}: {len(df.columns)} colonnes, "
                f"{config['colonnes']} attendues"
            )

        total_source = df.count()
        print("Lignes sources :", total_source)
        print("Colonnes :", len(df.columns))

        # 2. Normalisation sans supprimer de lignes
        silver = df.select([
            F.when(
                F.trim(F.col(c)) == "",
                F.lit(None)
            ).otherwise(F.trim(F.col(c))).alias(c)
            for c in df.columns
        ])

        # 3. Contrôle des valeurs manquantes
        stats = silver.agg(*[
            F.count(F.when(F.col(c).isNull(), 1)).alias(c)
            for c in silver.columns
        ]).first().asDict()

        print("Colonnes contenant des NULL :")
        for colonne, nombre in stats.items():
            if nombre > 0:
                print(f"  {colonne}: {nombre}")

        # 4. Contrôle des doublons complets
        total_distinct = silver.distinct().count()
        doublons = total_source - total_distinct

        print("Doublons complets :", doublons)

        # On conserve les lignes et signale les doublons.
        # La suppression nécessite une règle métier validée.

        # 5. Ecriture Parquet
        silver.write \
            .mode("errorifexists") \
            .option("compression", "snappy") \
            .parquet(config["destination"])

        # 6. Vérification après écriture
        controle = spark.read.parquet(
            config["destination"]
        )

        total_silver = controle.count()

        if total_silver != total_source:
            raise ValueError(
                f"{nom}: nombre de lignes différent "
                "après écriture"
            )

        print("Lignes Silver :", total_silver)
        print("Destination :", config["destination"])
        print("STATUT : OK")

finally:
    spark.stop()
