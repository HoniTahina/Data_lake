from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("Retail-UC06-Structure")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

fichier = "file:///home/honi/retail-tp3-input/store.dat"

df = (
    spark.read
    .option("header", "false")
    .option("sep", "|")
    .option("inferSchema", "false")
    .csv(fichier)
)

print("===== SCHEMA =====")
df.printSchema()

print("===== NOMBRE DE LIGNES =====")
print(df.count())

print("===== NOMBRE DE COLONNES =====")
print(len(df.columns))

print("===== PREMIERES LIGNES =====")
df.show(3, truncate=25)

print("===== VALEURS NULLES =====")
df.select([
    count(when(col(c).isNull() | (col(c) == ""), c)).alias(c)
    for c in df.columns
]).show(truncate=False)

spark.stop()
