# TP4 — UC-08 : Analyse décisionnelle

## 1. Contexte

Projet : Retail Intelligence Platform.

Environnement : Ubuntu WSL2, Hadoop HDFS,
PySpark, JupyterLab et Matplotlib.

Source : données synthétiques TPCx-BB.

## 2. Sources utilisées

- Silver : uc06_store_sales, uc06_item, uc06_store.
- Gold : uc06_finance_magasins, uc06_finance_articles.
- Format : Apache Parquet.
- Stockage : Hadoop HDFS.

## 3. Indicateurs calculés

- Nombre de lignes de ventes : 667 579.
- Quantité totale : 33 755 474.
- Montant des ventes : 1 277 224 004,61.
- Montant net : 1 150 529 586,37.
- Bénéfice calculé : -552 553 374,82.

Les montants sont présentés sans unité monétaire
confirmée.

## 4. Statistiques descriptives

Les 667 579 lignes de ventes ont été analysées.

- Moyenne : 1 913,22.
- Médiane approximative : 1 048,45.
- Minimum : 0,00.
- Maximum : 18 745,00.
- Écart-type : 2 281,75.

La moyenne est supérieure à la médiane,
ce qui suggère une distribution asymétrique
vers les valeurs élevées.

## 5. Analyse par magasin

Le magasin 7 présente le montant le plus élevé :
109 714 870,06.

Le magasin 2 présente le montant le plus faible :
104 610 803,14.

Les écarts observés ne prouvent pas une
différence de performance opérationnelle.

## 6. Analyse par article

L'article 10000 est le premier du classement :
17 132 394,87.

Le Top 10 représente 85 373 737,14,
soit 6,68 % du montant total des ventes.

## 7. Limites

- Données synthétiques.
- Unité monétaire non confirmée.
- Période d'analyse non documentée.
- Une ligne de vente n'est pas une transaction.
- Les retours ne sont pas analysés séparément.
- Les causes des écarts ne sont pas établies.

## 8. Recommandations

1. Examiner les différences de volume entre magasins.
2. Comparer les montants et quantités par article.
3. Vérifier les périodes et les catégories produits.
4. Compléter les indicateurs si des données
   supplémentaires sont disponibles.

## 9. Livrables

- Notebook Jupyter du TP4.
- Quatre fichiers CSV.
- Deux graphiques PNG.
- Rapport d'analyse métier.
