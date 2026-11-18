from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-Relations")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

base = "hdfs://localhost:9000/retail-lake/silver"

ventes = spark.read.parquet(
    f"{base}/uc06_store_sales"
)

articles = spark.read.parquet(
    f"{base}/uc06_item"
)

magasins = spark.read.parquet(
    f"{base}/uc06_store"
)

# Clés candidates, encore à confirmer
v = ventes.select(
    F.col("_c2").alias("cle_article"),
    F.col("_c7").alias("cle_magasin")
)

a = articles.select(
    F.col("_c0").cast("string").alias("cle_article")
)

m = magasins.select(
    F.col("_c0").cast("string").alias("cle_magasin")
)

print("===== UNICITE DES CLES =====")
print(
    "Articles :",
    a.count(),
    "clés distinctes :",
    a.distinct().count()
)

print(
    "Magasins :",
    m.count(),
    "clés distinctes :",
    m.distinct().count()
)

print("\n===== VALIDATION DES RELATIONS =====")
total = v.count()
print("Lignes de ventes :", total)

articles_trouves = v.join(
    a, on="cle_article", how="left_semi"
).count()

magasins_trouves = v.join(
    m, on="cle_magasin", how="left_semi"
).count()

print(
    "Ventes avec article correspondant :",
    articles_trouves,
    "/", total
)

print(
    "Ventes avec magasin correspondant :",
    magasins_trouves,
    "/", total
)

print("\n===== EXEMPLES DE CLES =====")
v.show(10, truncate=False)

spark.stop()
