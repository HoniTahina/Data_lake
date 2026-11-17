#!/usr/bin/env bash
set -u
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$BASE/environnement" "$BASE/hdfs" "$BASE/data_lake"
SOURCE='/mnt/d/Dev/M5/Data lake/Cours 1/Retail-project/retail_project/data/store/store.dat'
DEST='/retail-lake/raw/tpcxbb/initial/store.dat'
{
 echo '=== DATE ==='; date -Is
 echo '=== OS ==='; cat /etc/os-release
 echo '=== JAVA 17 ==='; /usr/lib/jvm/java-17-openjdk-amd64/bin/java -version
 echo '=== HADOOP ==='; hadoop version
 echo '=== PROCESSUS JAVA ==='; jps
 echo '=== CONFIGURATION ==='; hdfs getconf -confKey fs.defaultFS; hdfs getconf -confKey dfs.namenode.name.dir; hdfs getconf -confKey dfs.datanode.data.dir; hdfs getconf -confKey dfs.replication
} > "$BASE/environnement/01_environnement.txt" 2>&1
{
 echo '=== DATE ==='; date -Is
 echo '=== ETAT HDFS ==='; hdfs dfsadmin -report
 echo '=== RACINE ==='; hdfs dfs -ls /
 echo '=== DROITS ==='; hdfs dfs -ls -d /retail-lake /retail-lake/raw /retail-lake/raw/tpcxbb /retail-lake/raw/tpcxbb/initial
} > "$BASE/hdfs/02_etat_hdfs.txt" 2>&1
{
 echo '=== DATE ==='; date -Is
 echo '=== ARBORESCENCE ==='; hdfs dfs -ls -R /retail-lake
 echo '=== FICHIER SOURCE ==='; ls -lh "$SOURCE"; file "$SOURCE"
 echo '=== FICHIER HDFS ==='; hdfs dfs -ls -h "$DEST"
 echo '=== TAILLES ==='; wc -c "$SOURCE"; hdfs dfs -du -h "$DEST"
 echo '=== SHA-256 SOURCE ==='; sha256sum "$SOURCE"
 echo '=== SHA-256 HDFS ==='; hdfs dfs -cat "$DEST" | sha256sum
} > "$BASE/data_lake/03_depot_integrite.txt" 2>&1
printf 'Fichiers de preuves créés sous %s\n' "$BASE"
printf 'Vérifie les trois fichiers TXT et ajoute tes captures PNG.\n'
