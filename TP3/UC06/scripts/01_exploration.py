from pyspark.sql import SparkSession
from pathlib import Path

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-HDFS")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

base = Path(
    "/mnt/d/Dev/M5/Data lake/Cours 1/"
    "Retail-project/retail_project/data"
)

fichier = base / "store" / "store.dat"

df = spark.read.text(
    "hdfs://localhost:9000/retail-lake/raw/nifi/store.dat"
)

print("===== SCHEMA BRUT =====")
df.printSchema()

print("===== 5 PREMIERES LIGNES =====")
df.show(5, truncate=150)

print("===== NOMBRE DE LIGNES =====")
print(df.count())

spark.stop()
