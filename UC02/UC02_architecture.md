# UC-02 — Concevoir et justifier une architecture Data

**Projet :** Retail Intelligence Platform  
**Environnement de travail :** Windows 11 / WSL (Ubuntu)  
**Statut :** conception, sans déploiement technique  
**Références :** TP1.pdf, UC-02 (pages 13 à 17) ; résultats de l'UC-01.

## Étape A — Identifier les contraintes

### A.1 Contexte

Le projet doit permettre d'intégrer, conserver, préparer et exploiter les données réellement disponibles pour les analyses commerciales, les magasins et le contrôle de gestion. Les usages prioritaires portent sur le montant net des ventes (indicateur opérationnel hors retours), les transactions, le panier moyen, les quantités vendues et leur évolution temporelle.

### A.2 Contraintes relevées dans l'UC-01

| Dimension | Observation vérifiée ou limite | Conséquence de conception |
|---|---|---|
| Sources et formats | 23 fichiers `.dat` initiaux, dans 23 sous-dossiers ; `store_sales.dat` est un texte ASCII avec délimiteur `\|` et fins de ligne CRLF. Les autres encodages restent à vérifier. | Ingestion de fichiers délimités ; lecture robuste ; validation de structure et de l'encodage par source. |
| Volumes | Environ 978 Mo dans `data/` et 9,2 Mo dans `data_refresh/`. | Stockage initial raisonnable, mais architecture extensible et partitionnement à étudier. |
| Diversité métier | Ventes magasin/web, clients, produits, stocks, retours, navigation web, référentiels. | Organisation par source et domaine, puis création de données préparées adaptées aux usages. |
| Actualisations | `data_refresh/` contient 11 `.dat` et un CSV d'audit. Les ventes initiales et refresh partagent la date du 13/12/2005. | Historiser chaque lot et sa provenance ; contrôler les clés métier et les recouvrements avant consolidation. |
| Historique | Les clés de date des ventes initiales correspondent à la période du 01/01/2001 au 13/12/2005 ; le refresh va jusqu'au 31/12/2005. | Conserver date métier ET date d'ingestion ; détecter les périodes incomplètes. |
| Qualité | `item` : colonne 4 (`i_rec_end_date` selon la spécification consultée) vide sur 17 820/17 820 lignes ; autres manquants ponctuels. Sur `store_sales`, 4 136 occurrences supplémentaires d'une clé candidate date/magasin/ticket/produit, sans ligne complète identique. | Contrôles de complétude, typage, clés et anomalies ; ne pas supprimer automatiquement les lignes ou les valeurs absentes. |
| Références | Cinq rapprochements de clés entre ventes, produits, magasins et dates n'ont révélé aucune référence absente dans les fichiers initiaux. | Réutiliser et étendre les validations référentielles dans la zone préparée. |
| Consommateurs | Direction commerciale, responsable de magasin, contrôleur de gestion. | Tables analytiques dédiées aux KPI et filtres temporels, produit, canal, magasin. |
| Confidentialité | Tables comportant des informations de clients ; sensibilité des champs à qualifier. | Accès restreints, minimisation, règles de conservation et suivi des usages. |
| Coûts et exploitation | Projet pédagogique local sous WSL, puis cible cloud étudiée. | Séparer le prototype local de la cible Azure ; prévoir supervision et contrôle des volumes. |

### A.3 Exemple de risque identifié

Le calcul de décembre 2005 sur les données initiales seules donnait -57,48 % par rapport à novembre. L'ajout des montants issus du refresh donne un résultat calculé de +4,32 %, sous réserve des hypothèses d'unicité des transactions et de complétude des lots. L'architecture doit tracer les lots, la couverture temporelle et les règles de consolidation.

### A.4 Hypothèses à valider

- Les règles exactes de mise à jour des différentes tables du refresh (ajout, remplacement, correction) ne sont pas confirmées pour toutes les sources.
- Les contrôles de qualité menés en UC-01 ne couvrent pas toutes les colonnes et toutes les tables.
- La devise, la méthode comptable du chiffre d'affaires et la prise en compte des retours restent à préciser.
- Les performances des outils envisagés ne sont pas mesurées ; leur positionnement constitue une proposition de conception.

## Étape B — Comparer les approches architecturales

### B.1 Data Warehouse

**Principe :** intégrer des données structurées dans un modèle analytique gouverné, souvent dimensionnel, afin d'optimiser les requêtes de reporting.

**Données adaptées :** ventes préparées, dimensions produits, magasins et dates, tables d'indicateurs.

**Avantages :** cohérence des calculs, modèle clair pour les utilisateurs métier, requêtes SQL et tableaux de bord.

**Limites :** le chargement de données hétérogènes et la conservation fidèle des `.dat` et des fichiers refresh exigent une étape amont ; les évolutions de schéma peuvent demander des adaptations.

**Usages :** suivi commercial, comparaison des magasins, analyses historiques et consolidation des KPI.

**Gouvernance :** schémas, définitions des indicateurs, règles de mise à jour, accès aux tables et lignage.

**Pertinence :** utile pour la restitution des KPI, mais moins naturel comme unique stockage pour l'ensemble des fichiers sources.

### B.2 Data Lake en zones

**Principe :** conserver les fichiers d'origine et organiser les traitements progressifs en zones Raw/Bronze, Silver et Gold.

**Données adaptées :** fichiers `.dat`, CSV d'audit, sources structurées, données de navigation et transformations au format Parquet.

**Avantages :** conservation des originaux, prise en charge de sources variées, historisation des lots, possibilité de retraiter les données depuis le brut.

**Limites :** requiert un catalogage et des contrôles de qualité pour éviter un lac de données désorganisé ; les fonctionnalités transactionnelles sur tables ne sont pas implicites.

**Usages :** ingestion batch des 23 sources et des actualisations ; contrôles ; préparation ; production de KPI.

**Gouvernance :** conventions de nommage, versions de schéma, métadonnées de provenance, contrôle des accès, qualité et suivi des flux.

**Pertinence :** très bonne compte tenu des fichiers réellement observés et des objectifs du parcours.

### B.3 Lakehouse

**Principe :** conserver une base de type Data Lake tout en y ajoutant, selon la technologie choisie, une gestion de tables permettant des opérations plus avancées (transactions, versions, mises à jour, etc.).

**Données adaptées :** données brutes et préparées, tables analytiques nécessitant des actualisations fréquentes.

**Avantages :** meilleure prise en charge possible des mises à jour et des tables analytiques au sein du stockage de type lac ; diminution potentielle des copies.

**Limites :** composants supplémentaires, complexité opérationnelle, contraintes liées au format de tables retenu.

**Usages :** consolidation de refresh, indicateurs historiques, exploration et BI.

**Gouvernance :** sécurité, catalogage, règles de qualité, gestion des versions et contrôles transactionnels.

**Pertinence :** évolution envisageable si les besoins de mise à jour et d'exploitation le justifient. Delta Lake reste facultatif dans le TP.

### B.4 Comparaison synthétique

| Critère | Data Warehouse | Data Lake en zones | Lakehouse |
|---|---|---|---|
| Fichiers bruts `.dat` | Zone amont à prévoir | Conservation native | Conservation possible |
| Variété des domaines | Après intégration | Très approprié | Très approprié |
| KPI et BI | Très approprié | Via couche Gold préparée | Très approprié |
| Gestion des refresh | Via traitements ETL/ELT | Contrôles et traitements à définir | Fonctions de mise à jour selon technologie |
| Gouvernance | Schémas et modèles | Forte discipline de catalogage | Catalogage et gestion de tables |
| Complexité du socle pédagogique | Dépend de l'outil retenu | Compatible avec HDFS, NiFi, Spark | Plus élevée si couche transactionnelle ajoutée |
| Pertinence pour le projet | Bonne pour servir les données | **Choix principal proposé** | Évolution facultative |

### B.5 Choix justifié

**Architecture recommandée : Data Lake en trois zones, Bronze/Raw → Silver → Gold.** Elle correspond à la diversité des fichiers effectivement disponibles et à la nécessité de conserver les lots initiaux et refresh, tout en séparant les contrôles de qualité des calculs métier.

- **Bronze/Raw :** conservation des fichiers sans modification, avec métadonnées de source, nom de fichier et lot.
- **Silver :** extraction et typage des colonnes, contrôles de structure et de références, traitement explicite des champs manquants, préparation en Parquet.
- **Gold :** tables de ventes consolidées, dimensions et agrégations nécessaires aux cinq KPI.

Le Data Warehouse peut compléter Gold pour une restitution SQL/BI ultérieure. Un Lakehouse est une extension possible, mais n'est pas requis pour valider le socle de ce TP.

**Statut :** architecture proposée ; ni déploiement ni performance d'exécution n'ont été validés à ce stade.

## Prochaines sections à développer

- Étape C : architecture logique et diagramme complet.
- Étape D : positionnement des composants (obligatoires / étudiés / facultatifs).
- Étape E : description des flux principaux.
- Étape F : gouvernance et contrôles.
- Étape G : déclinaison locale WSL et cible Azure ADLS Gen2.
