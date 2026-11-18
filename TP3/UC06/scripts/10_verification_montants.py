from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-Verification-Montants")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    source = (
        "hdfs://localhost:9000/retail-lake/"
        "silver/uc06_store_sales"
    )

    df = spark.read.parquet(source)

    colonnes = {
        "_c10": "quantite_candidate",
        "_c13": "prix_unitaire_candidat",
        "_c15": "montant_ventes_candidat",
        "_c20": "montant_net_candidat",
        "_c22": "benefice_candidat"
    }

    # Conversion tolérante pour repérer les valeurs invalides
    for origine, nouveau in colonnes.items():
        df = df.withColumn(
            nouveau,
            F.expr(
                f"try_cast({origine} as decimal(18,2))"
            )
        )

    print("===== TYPES NUMERIQUES =====")
    df.select(*colonnes.values()).printSchema()

    print("===== EXEMPLES =====")
    df.select(*colonnes.values()).show(
        10, truncate=False
    )

    print("===== VALEURS NON CONVERTIBLES =====")
    for origine, nouveau in colonnes.items():
        invalides = df.filter(
            F.col(origine).isNotNull()
            & F.col(nouveau).isNull()
        ).count()

        print(nouveau, ":", invalides)

    # Hypothèse : montant des ventes =
    # quantité × prix unitaire
    controle = df.filter(
        F.col("quantite_candidate").isNotNull()
        & F.col("prix_unitaire_candidat").isNotNull()
        & F.col("montant_ventes_candidat").isNotNull()
    )

    ecarts = controle.filter(
        F.abs(
            F.col("quantite_candidate")
            * F.col("prix_unitaire_candidat")
            - F.col("montant_ventes_candidat")
        ) > F.lit(0.01)
    ).count()

    print("===== COHERENCE DES MONTANTS =====")
    print("Lignes testables :", controle.count())
    print("Ecarts supérieurs à 0,01 :", ecarts)

finally:
    spark.stop()
