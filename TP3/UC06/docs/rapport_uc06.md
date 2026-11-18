# TP3 — UC-06
## Retail Intelligence Platform

### 1. Objectif
Construire un pipeline de transformation de données
TPCx-BB avec Hadoop HDFS, PySpark et Parquet.

Architecture :
Raw → Silver → Gold

### 2. Environnement
- Ubuntu WSL2
- Hadoop HDFS
- Python et PySpark 4.3.0
- Format Parquet, compression Snappy

### 3. Données sources
Le jeu de données initial contient 23 tables.

Tables utilisées :
- store : 12 lignes
- item : 17 820 lignes
- store_sales : 667 579 lignes

### 4. Transformations Silver
Trois tables ont été produites dans HDFS.

Traitements réalisés :
- Lecture des fichiers séparés par |
- Contrôle du nombre de colonnes
- Normalisation des champs vides
- Vérification des doublons complets
- Conversion de certains champs
- Stockage au format Parquet

Limite :
Le typage métier complet reste à documenter.

### 5. Contrôles des jointures
Clés candidates testées :
- store_sales._c2 = item._c0
- store_sales._c7 = store._c0

Résultats :
- 667 579 lignes sources
- 667 579 lignes après jointures
- 100 % de correspondances sur les clés testées

### 6. Agrégations Gold
Quatre tables produites :
- uc06_ventes_magasins
- uc06_ventes_articles
- uc06_finance_magasins
- uc06_finance_articles

### 7. Résultats financiers calculés
- Lignes de ventes : 667 579
- Quantités : 33 755 474
- Montant des ventes : 1 277 224 004.61
- Montant net : 1 150 529 586.37
- Bénéfice calculé : -552 553 374.82

Ces indicateurs utilisent des correspondances
de colonnes cohérentes avec les tests, mais
leur définition métier et leur unité monétaire
restent à confirmer.

### 8. Contrôles qualité finaux
- Lignes invalides selon les tests : 0
- Écarts quantité × prix : 0
- Totaux magasins / articles identiques : oui
- Conservation des lignes : oui
- Relecture des fichiers Parquet : réussie

Rapport :
quality/rapport_final_qualite.json

### 9. Limites et améliorations
- Vérifier le schéma métier officiel.
- Compléter le typage des colonnes Silver.
- Documenter les règles de traitement des NULL.
- Analyser les bénéfices négatifs.
- Ajouter des contrôles de qualité reproductibles.
- Comparer le stockage brut et Parquet.

### 10. Conclusion
Le pipeline Raw → Silver → Gold est fonctionnel
sur les trois tables sélectionnées.

Les contrôles techniques effectués sont
satisfaisants. La validation métier complète
reste à réaliser.

### 11. Comparaison des formats Raw et Parquet

| Table | Raw (octets) | Silver (octets) | Réduction |
|---|---:|---:|---:|
| store | 3 386 | 10 451 | -208,65 % |
| item | 6 799 286 | 3 641 846 | 46,44 % |
| store_sales | 92 764 700 | 45 532 130 | 50,92 % |

Au total, le stockage passe de 99 567 372 octets
en Raw à 49 184 427 octets en Silver,
soit une réduction globale de 50,61 %.

Le petit fichier store présente une augmentation
de taille en Parquet, liée notamment au poids
des métadonnées et de la structure du fichier.

Cette comparaison porte sur les tailles de stockage
et ne démontre pas un gain de vitesse de traitement.
