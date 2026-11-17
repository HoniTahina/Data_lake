# UC-01 — Cadrage métier et exploration des sources TPCx-BB

**Projet :** Retail Intelligence Platform  
**Environnement d'exploration :** Ubuntu sous WSL  
**Jeu de données :** TPCx-BB, dossiers `data/` et `data_refresh/`  
**Statut :** rapport d'exploration révisé avec les définitions officielles TPCx-BB v1.7.0 ; certains contrôles complémentaires restent à réaliser.

## 1. Objet, méthode et conventions

L'objectif de cette première étude est d'identifier les besoins des utilisateurs métier, de définir des indicateurs décisionnels, de dresser un inventaire des fichiers disponibles et d'évaluer la qualité et les relations principales des données avant la conception de l'architecture cible (UC-02).

L'exploration repose sur les sorties de commandes WSL communiquées lors du TP (`find`, `du`, `wc`, `head`, `file`, `awk`, `sort`, `uniq`, `comm`, `stat`). Les mesures ci-dessous proviennent de ces sorties et non d'un nouvel accès direct aux fichiers `.dat`. Les noms, positions et types techniques des champs présentés ci-après sont tirés des définitions `CREATE EXTERNAL TABLE` de la **spécification officielle TPCx-BB v1.7.0 (juin 2025, annexe I, pages 123 à 135)**. Leur nombre correspond aux structures observées dans les fichiers locaux pour les tables citées. La version exacte du générateur ayant produit les `.dat` reste à confirmer ; les types ci-dessous sont ceux du schéma Hive de référence, **et non des types mesurés dans des colonnes textuelles**.

**Convention financière :** dans ce rapport, « CA hors retours » signifie **somme des champs `ss_net_paid` et/ou `ws_net_paid`**, sans soustraction des retours et sans affirmation de conformité à une définition comptable du CA. L'unité monétaire du jeu généré n'a pas été confirmée : les résultats ne sont donc **pas libellés en euros**.

## 2. Étape A — Comprendre les utilisateurs et les décisions

Les sources indiquées dans ce tableau sont les sources *envisagées* pour répondre aux questions, et non la preuve qu'une analyse complète a déjà été menée.

| Profil | Question décisionnelle | Décision associée | Priorité | Sources envisagées |
|---|---|---|---|---|
| **Direction commerciale** | Quels produits génèrent le plus de montant net payé et quelles quantités sont vendues ? | Renforcer, repositionner ou retirer une gamme | Indispensable | `store_sales`, `web_sales`, `item` |
| Direction commerciale | Quel est le poids des canaux magasin et web ? | Répartir l'effort commercial et marketing | Indispensable | `store_sales`, `web_sales` |
| **Responsable de magasin** | Comment évoluent les ventes de mon magasin dans le temps ? | Adapter l'organisation commerciale et, avec les données adéquates, les effectifs | Indispensable | `store_sales`, `store`, `date_dim` |
| Responsable de magasin | Comment se situe mon magasin par rapport aux autres ? | Identifier les écarts et bonnes pratiques | Utile | `store_sales`, `store` |
| **Contrôleur de gestion** | Quel est le montant net des ventes par période et par canal, et par magasin pour le canal physique ? | Réviser les prévisions et budgets | Indispensable | `store_sales`, `web_sales`, `date_dim`, `store` |
| Contrôleur de gestion | Comment évoluent les ventes des produits associés à des promotions ? | Réexaminer les campagnes et décider d'analyses plus poussées | Utile | `promotion`, `store_sales`, `web_sales` |

**Précision :** une comparaison descriptive des ventes de produits en promotion ne suffit pas à prouver que la promotion a *causé* une augmentation des ventes.

## 3. Étape B — Dictionnaire des cinq indicateurs

### KPI 1 — Montant net des ventes, appelé « CA hors retours » dans l'étude

- **Définition métier :** montant total net payé pour les lignes de vente réalisées sur une période, sans retraitement des retours.
- **Formule :** `SUM(ss_net_paid)` pour les magasins ; `SUM(ws_net_paid)` pour le web ; somme des deux canaux pour la consolidation.
- **Unité :** unité monétaire non confirmée.
- **Périmètre :** canal, période ; magasin pour les ventes physiques ; consolidation de l'enseigne.
- **Fréquence :** quotidienne, mensuelle, annuelle.
- **Sources :** `store_sales`, `web_sales`, `date_dim` et éventuellement `store`.
- **Informations manquantes / à valider :** devise, règles de gestion comptable, traitement des annulations et retours ; intégration définitive des actualisations.
- **Limites d'interprétation :** la mesure est issue des champs « net paid » et ne représente pas nécessairement le chiffre d'affaires comptable hors taxes ou après retours.

### KPI 2 — Nombre de transactions / commandes

- **Définition métier :** nombre de tickets distincts en magasin et de commandes distinctes sur le web.
- **Formule :** nombre de combinaisons distinctes `(ss_sold_date_sk, ss_store_sk, ss_ticket_number)` pour le magasin ; nombre distinct de `ws_order_number` pour le web ; addition des décomptes des deux canaux.
- **Unité :** tickets ou commandes.
- **Périmètre :** canal et période, avec détail par magasin pour le physique.
- **Fréquence :** quotidienne et mensuelle.
- **Sources :** `store_sales`, `web_sales`, `date_dim`.
- **Informations manquantes / à valider :** unicité métier définitive de la clé candidate du magasin ; règles de gestion des commandes annulées et des retours.
- **Limites d'interprétation :** plusieurs lignes peuvent relever du même ticket ou de la même commande ; une ligne ne doit pas être assimilée à une transaction.

### KPI 3 — Panier moyen

- **Définition métier :** montant net payé moyen par ticket ou commande.
- **Formule :** `CA hors retours / nombre de tickets ou commandes distincts` sur le même périmètre.
- **Unité :** unité monétaire par ticket ou commande.
- **Périmètre :** magasins, web, consolidé, par période.
- **Fréquence :** quotidienne et mensuelle.
- **Sources :** `store_sales`, `web_sales`, `date_dim`.
- **Informations manquantes / à valider :** règles d'annulation, de retour et de décompte des transactions.
- **Limites d'interprétation :** le panier moyen dépend du périmètre et de la définition des transactions ; il est indéfini si leur nombre est nul.

### KPI 4 — Quantités vendues

- **Définition métier :** nombre total d'unités d'articles enregistrées comme vendues.
- **Formule :** `SUM(ss_quantity)` pour le magasin et `SUM(ws_quantity)` pour le web.
- **Unité :** unités d'articles.
- **Périmètre :** produit, catégorie, canal, période et magasin pour le physique.
- **Fréquence :** quotidienne, hebdomadaire, mensuelle.
- **Sources :** `store_sales`, `web_sales`, `item`, `date_dim`.
- **Informations manquantes / à valider :** unités particulières éventuelles, quantités retournées, dimensions produit.
- **Limites d'interprétation :** le volume ne mesure ni la marge ni la valeur des ventes ; ici les retours ne sont pas déduits.

### KPI 5 — Évolution mensuelle du montant net des ventes

- **Définition métier :** taux de variation du montant net payé par rapport au mois précédent.
- **Formule :** `(CA_mois_courant - CA_mois_précédent) / CA_mois_précédent × 100`.
- **Unité :** %.
- **Périmètre :** canaux séparés ou consolidés, mois comparables.
- **Fréquence :** mensuelle (une comparaison annuelle peut être ajoutée).
- **Sources :** `store_sales`, `web_sales`, `date_dim`, puis `data_refresh` après contrôle des clés.
- **Informations manquantes / à valider :** complétude des périodes et exhaustivité des fichiers d'actualisation.
- **Limites d'interprétation :** saisonnalité, durées inégales des mois, promotions et périodes partielles ; taux indéfini si le montant précédent est nul.

### Récapitulatif des formules

| Indicateur | Formule synthétique | Fréquence privilégiée |
|---|---|---|
| Montant net des ventes (« CA hors retours ») | `Σ montants nets payés` | Jour / mois |
| Nombre de transactions | `COUNT DISTINCT` des tickets ou commandes, selon le canal | Jour / mois |
| Panier moyen | `Montant net payé / transactions` | Jour / mois |
| Quantités vendues | `Σ quantités` | Jour / mois |
| Évolution du CA | `(CA courant − CA précédent) / CA précédent × 100` | Mois |

## 4. Étape C — Inventaire physique des sources

### 4.1 Données initiales : dossier `data/`

Les commandes ont identifié **23 fichiers `.dat`**, répartis dans 23 sous-dossiers, pour **environ 978 Mo selon `du -sh .`**. Le nombre de champs ci-dessous correspond à la **première ligne**, et non à une validation de l'ensemble de chaque fichier.

| Source | Lignes (`wc -l`) | Champs, 1re ligne | Taille affichée par `du -h` |
|---|---:|---:|---:|
| `customer` | 99 000 | 18 | 13M |
| `customer_address` | 49 500 | 13 | 5.2M |
| `customer_demographics` | 1 920 800 | 9 | 75M |
| `date_dim` | 109 573 | 28 | 15M |
| `household_demographics` | 7 200 | 5 | 152K |
| `income_band` | 20 | 3 | 0 (affichage `du`) |
| `inventory` | 23 255 100 | 4 | 406M |
| `item` | 17 820 | 22 | 6.5M |
| `item_marketprices` | 89 100 | 6 | 4.1M |
| `product_reviews` | 89 991 | 8 | 54M |
| `promotion` | 300 | 19 | 48K |
| `reason` | 35 | 3 | 4.0K |
| `ship_mode` | 20 | 6 | 4.0K |
| `store` | 12 | 29 | 4.0K |
| `store_returns` | 37 902 | 20 | 4.2M |
| `store_sales` | 667 579 | 23 | 89M |
| `time_dim` | 86 400 | 10 | 4.9M |
| `warehouse` | 5 | 14 | 1.0K |
| `web_clickstreams` | 6 770 550 | 6 | 171M |
| `web_page` | 60 | 14 | 8.0K |
| `web_returns` | 38 487 | 24 | 5.2M |
| `web_sales` | 668 052 | 34 | 128M |
| `web_site` | 30 | 26 | 12K |

**Précision sur les tailles :** `income_band.dat` contient effectivement **327 octets**, confirmés par `stat`, malgré un affichage `du -h` égal à `0` sur le système monté.

Les fichiers représentent notamment les domaines vente, client, produit, stock, retours, calendrier et parcours web. La présence de fichiers volumineux tels que `inventory` et `web_clickstreams` est pertinente pour les choix d'ingestion et de stockage de l'UC-02.

### 4.2 Données complémentaires : dossier `data_refresh/`

La recherche a identifié **11 fichiers `.dat` et un CSV d'audit** (`item_marketprices_audit.csv`), pour **9,2 Mo selon `du -sh`**.

| Source refresh | Lignes | Champs sur la 1re ligne |
|---|---:|---:|
| `customer` | 1 000 | 18 |
| `customer_address` | 500 | 13 |
| `inventory` | 234 900 | 4 |
| `item` | 180 | 22 |
| `item_marketprices` | 900 | 6 |
| `product_reviews` | 909 | 8 |
| `store_returns` | 426 | 20 |
| `store_sales` | 6 632 | 23 |
| `web_clickstreams` | 68 988 | 6 |
| `web_returns` | 400 | 24 |
| `web_sales` | 6 879 | 34 |

Les 11 fichiers `.dat` de refresh ont, sur leur première ligne, le même nombre de champs que leurs homologues de `data/`. Cela **ne prouve pas** que les types et les règles métier sont identiques. L'hypothèse d'une alimentation complémentaire est étayée pour les ventes par l'analyse des dates et des identifiants, mais n'est pas vérifiée de manière exhaustive pour les autres tables.

## 5. Étape D — Structure, complétude et granularité

### 5.1 Format des fichiers

Le fichier `store_sales/store_sales.dat` a été reconnu par `file` comme **texte ASCII avec fins de ligne CRLF**. Ses premières lignes sont délimitées par `|` et ne présentent pas d'en-tête. Le séparateur et les fins de ligne n'ont pas été contrôlés exhaustivement pour l'ensemble des 23 fichiers.

### 5.2 Contrôle de structure et de champs vides sur échantillon

Les **1 000 premières lignes** de cinq fichiers ont un nombre de champs stable :

| Source | Champs par ligne sur l'échantillon | Champs vides | Total champs examinés | Taux vide |
|---|---:|---:|---:|---:|
| `store_sales` | 23 | 0 | 23 000 | 0 % |
| `web_sales` | 34 | 1 | 34 000 | 0,0029 % |
| `customer` | 18 | 2 | 18 000 | 0,0111 % |
| `item` | 22 | 1 001 | 22 000 | 4,55 % |
| `inventory` | 4 | 0 | 4 000 | 0 % |

**Limite :** l'échantillonnage porte sur les premières lignes (non aléatoires) ; on ne peut pas extrapoler ces taux à tout le fichier.

### 5.3 Contrôle complet des champs vides de `item`

La lecture des **17 820 lignes** (22 champs) a permis de mesurer **17 838 champs vides sur 392 040**, soit **4,55 %** :

| Position | Champs vides | Part des 17 820 lignes |
|---|---:|---:|
| 4 | 17 820 | 100 % |
| 5 | 4 | 0,02 % |
| 8 | 8 | 0,04 % |
| 9 | 6 | 0,03 % |
| Autres positions | 0 | 0 % |

**Interprétation désormais documentée :** la position 4 correspond à `i_rec_end_date` (`STRING` dans le DDL Hive), soit la date de fin de validité d’une version de produit. Elle n’est pas marquée `NOT NULL` dans la spécification. Son absence dans les 17 820 lignes peut donc être cohérente avec des versions de produit encore valides ; la raison précise de ce taux de 100 % dans cet export n’est toutefois **pas confirmée**. Les positions 5, 8 et 9 correspondent respectivement à `i_item_desc` (`STRING`), `i_brand_id` (`INT`) et `i_brand` (`STRING`). Aucune suppression ni imputation n’a été effectuée.

### 5.4 Doublons et granularité des ventes magasin

Dans `store_sales` initial :

- **667 579 lignes** de vente.
- **89 100 tickets distincts** selon la clé candidate `(date, magasin, numéro de ticket)`.
- **4 136 occurrences supplémentaires** d'une combinaison `(date, magasin, ticket, produit)` déjà rencontrée.
- **0 ligne complète répétée** selon la comparaison textuelle effectuée.
- Les 4 136 occurrences supplémentaires diffèrent de la première ligne portant la même clé candidate.

**Conclusion :** la combinaison `(date, magasin, ticket, produit)` n'identifie pas une ligne de manière unique dans ce fichier. En revanche, ces répétitions ne sont pas des doublons de ligne complète et **ne doivent pas être supprimées automatiquement**. La granularité et la clé technique définitive restent à documenter.

### 5.5 Schémas officiels de référence : noms, ordre et types des colonnes

**Source vérifiée :** TPC, *TPCx-BB Standard Specification*, version 1.7.0, juin 2025, annexe I (pages imprimées 123 à 135). Les types ci-dessous sont ceux des définitions Hive `CREATE EXTERNAL TABLE`. Ils ne signifient pas que les fichiers `.dat` stockent physiquement des valeurs binaires `BIGINT` ou `DECIMAL` : ce sont des fichiers texte à convertir lors de l'ingestion.

L'annexe associée `UC01_colonnes_types_TPCxBB.csv` contient le **dictionnaire de 111 colonnes** pour les cinq tables centrales suivantes : `store_sales` (23), `web_sales` (34), `item` (22), `inventory` (4) et `date_dim` (28). Les nombres concordent avec les nombres de champs relevés sur la première ligne des fichiers locaux. Les schémas complets des 18 autres tables ne sont pas transcrits dans cette annexe et restent à compléter si le TP exige un dictionnaire exhaustif de toutes les tables.

#### 5.5.1 Colonnes structurantes et correspondance avec les KPI

| Table | Position | Nom officiel | Type de référence | Utilisation |
|---|---:|---|---|---|
| `store_sales` | 1 | `ss_sold_date_sk` | `BIGINT` | Date, jointure avec `date_dim` |
| `store_sales` | 3 | `ss_item_sk` | `BIGINT` | Produit, jointure avec `item` |
| `store_sales` | 8 | `ss_store_sk` | `BIGINT` | Magasin |
| `store_sales` | 10 | `ss_ticket_number` | `BIGINT` | Ticket / transaction |
| `store_sales` | 11 | `ss_quantity` | `INT` | Quantités vendues |
| `store_sales` | 14 | `ss_sales_price` | `DECIMAL(7,2)` | Prix unitaire |
| `store_sales` | 21 | `ss_net_paid` | `DECIMAL(7,2)` | Montant net hors retours |
| `web_sales` | 1 | `ws_sold_date_sk` | `BIGINT` | Date |
| `web_sales` | 4 | `ws_item_sk` | `BIGINT` | Produit |
| `web_sales` | 18 | `ws_order_number` | `BIGINT` | Commande web |
| `web_sales` | 19 | `ws_quantity` | `INT` | Quantités vendues |
| `web_sales` | 22 | `ws_sales_price` | `DECIMAL(7,2)` | Prix unitaire |
| `web_sales` | 30 | `ws_net_paid` | `DECIMAL(7,2)` | Montant net hors retours |
| `item` | 1 | `i_item_sk` | `BIGINT` | Clé produit |
| `item` | 4 | `i_rec_end_date` | `STRING` | Fin de validité, champ facultatif dans le DDL |
| `item` | 5 | `i_item_desc` | `STRING` | Description produit |
| `item` | 8 | `i_brand_id` | `INT` | Identifiant marque |
| `item` | 9 | `i_brand` | `STRING` | Marque |
| `date_dim` | 1 | `d_date_sk` | `BIGINT` | Clé calendrier |
| `date_dim` | 3 | `d_date` | `STRING` | Date au format `AAAA-MM-JJ` dans le fichier |
| `inventory` | 4 | `inv_quantity_on_hand` | `INT` | Stock enregistré |

#### 5.5.2 Requalification des valeurs manquantes dans `item`

| Champ identifié | Position | Vides / 17 820 | Type de référence | Lecture prudente |
|---|---:|---:|---|---|
| `i_rec_end_date` | 4 | 17 820 | `STRING` | Date de fin non renseignée ; autorisée par le DDL, explication précise du 100 % non confirmée |
| `i_item_desc` | 5 | 4 | `STRING` | Description absente ; caractère anormal à confirmer selon les règles métier |
| `i_brand_id` | 8 | 8 | `INT` | Identifiant de marque absent ; contrôler la cohérence avec `i_brand` |
| `i_brand` | 9 | 6 | `STRING` | Libellé de marque absent ; contrôler la cohérence avec `i_brand_id` |

La spécification désigne explicitement `i_item_sk` et `i_item_id` comme `NOT NULL` dans cette table. Elle ne qualifie pas les quatre champs ci-dessus de `NOT NULL`. **Une colonne à 100 % vide n'implique donc pas automatiquement une erreur de génération.**

#### 5.5.3 Impact sur l'analyse

Les formules des KPI déjà calculés restent **inchangées**, puisque les positions de `ss_net_paid`, `ws_net_paid`, des quantités et des identifiants de transaction sont cohérentes avec la spécification. En revanche, les anciennes formulations « noms de colonnes inconnus » doivent être remplacées par « noms et types identifiés dans le schéma officiel, compatibilité à confirmer sur tous les fichiers ». La comptabilisation des retours, la devise et les règles d'annulation restent non vérifiées.

## 6. Étape E — Relations entre sources et cohérence référentielle

Les positions de champs ont été rapprochées des définitions TPCx-BB et contrôlées sur les données initiales :

| Source | Champ / position testée | Référence testée | Références distinctes absentes |
|---|---|---|---:|
| `store_sales` | `ss_item_sk` / 3 | `item.i_item_sk` / 1 | 0 |
| `store_sales` | `ss_store_sk` / 8 | `store.s_store_sk` / 1 | 0 |
| `store_sales` | `ss_sold_date_sk` / 1 | `date_dim.d_date_sk` / 1 | 0 |
| `web_sales` | `ws_item_sk` / 4 | `item.i_item_sk` / 1 | 0 |
| `web_sales` | `ws_sold_date_sk` / 1 | `date_dim.d_date_sk` / 1 | 0 |

Les identifiants examinés dans `item` et `store` (position 1) ne présentent **aucun doublon de valeur**. Ces vérifications montrent que les références testées sont présentes et que les deux clés de dimension testées sont uniques. Elles ne prouvent pas l'intégrité référentielle de **toutes** les tables ni celle des fichiers refresh.

## 7. Étape F — Comparaison temporelle initial / refresh

La première colonne de `store_sales` et de `web_sales` correspond aux clés de dates relevées dans `date_dim` :

| Clé | Date dans `date_dim` |
|---|---|
| 36890 | 01/01/2001 |
| 38697 | 13/12/2005 |
| 38715 | 31/12/2005 |

Les deux canaux ont les **mêmes bornes observées** :

| Jeu | Minimum | Maximum | Période correspondante |
|---|---:|---:|---|
| Initial | 36890 | 38697 | 01/01/2001 – 13/12/2005 |
| Refresh | 38697 | 38715 | 13/12/2005 – 31/12/2005 |

La **date frontière du 13 décembre 2005** figure dans les deux jeux : 285 lignes magasin et 275 lignes web côté initial ; 96 lignes magasin et 101 lignes web côté refresh. Une date commune ne signifie pas que les transactions sont les mêmes.

Contrôles de chevauchement effectués :

- `store_sales` : **0 ticket commun** entre initial et refresh, selon `(date, magasin, ticket)` ; **89 100** tickets initiaux et **900** tickets refresh distincts.
- `web_sales` : **0 numéro de commande commun** entre initial et refresh, selon `ws_order_number`.
- `store_sales` : **0 ligne textuellement identique** entre les deux jeux, selon `sort -u` et `comm`.

Ces résultats sont **compatibles avec un prolongement de la période de vente**, sous réserve de la validité des clés et de la complétude de l'actualisation. Les fichiers originaux ont été conservés séparés pendant l'exploration.

## 8. Étape G — Calculs des KPI et analyses

### 8.1 Résultats sur les seules données initiales

Les calculs ont utilisé les positions suivantes, cohérentes avec le schéma examiné :

| Champ | Magasin | Web |
|---|---|---|
| Date | 1 — `ss_sold_date_sk` | 1 — `ws_sold_date_sk` |
| Produit | 3 — `ss_item_sk` | 4 — `ws_item_sk` |
| Ticket / commande | 10 — `ss_ticket_number` (avec date et magasin) | 18 — `ws_order_number` |
| Quantité | 11 — `ss_quantity` | 19 — `ws_quantity` |
| Prix de vente unitaire | 14 — `ss_sales_price` | 22 — `ws_sales_price` |
| Montant net payé | 21 — `ss_net_paid` | 30 — `ws_net_paid` |

Les premières lignes présentent une cohérence arithmétique : `31 × 23,08 = 715,48` dans `store_sales` et `93 × 59,29 = 5 513,97` dans `web_sales`. Ce contrôle ponctuel ne valide pas toutes les lignes.

| KPI | Magasin | Web | Consolidé |
|---|---:|---:|---:|
| Montant net payé hors retours | 1 150 529 586,37 | 1 535 374 825,67 | **2 685 904 412,04** |
| Tickets / commandes distincts | 89 100 | 89 100 | **178 200** |
| Panier moyen | 12 912,79 | 17 232,04 | **15 072,42** |
| Quantités vendues | 33 755 474 | 33 724 378 | **67 479 852** |

Le panier moyen consolidé est calculé par `2 685 904 412,04 / 178 200 = 15 072,42` après arrondi. Les montants ne sont pas étiquetés en euros ; les quantités et montants restent **avant déduction des retours**. Ces totaux excluent `data_refresh`.

### 8.2 Évolution mensuelle : enseignement sur les périodes incomplètes

Pour les données initiales, les calculs mensuels font notamment apparaître :

| Période | Montant net payé | Variation mensuelle |
|---|---:|---:|
| Janvier 2001 | 45 659 605,05 | — |
| Février 2001 | 42 195 962,36 | −7,59 % |
| Mars 2001 | 46 882 188,75 | +11,11 % |
| Janvier 2002 | 45 783 132,92 | +2,97 % |
| Février 2002 | 41 346 610,18 | −9,69 % |
| Mars 2002 | 46 728 853,08 | +13,02 % |
| Novembre 2005 | 44 185 561,99 | −2,31 % |
| Décembre 2005, initial seul | 18 787 578,14 | **−57,48 % (non comparable)** |

Le mois de **décembre 2005 est incomplet dans les données initiales**, qui s'arrêtent au 13 décembre. La baisse apparente de 57,48 % **ne doit pas être interprétée comme une chute réelle d'activité**.

### 8.3 Calcul complémentaire de décembre 2005 avec refresh

| Composante | Montant net payé |
|---|---:|
| Décembre, données initiales | 18 787 578,14 |
| Décembre, refresh magasin (6 632 lignes) | 11 544 261,51 |
| Décembre, refresh web (6 879 lignes) | 15 764 416,32 |
| **Décembre consolidé sous hypothèse d'addition** | **46 096 255,97** |

Le taux recalculé par rapport à novembre 2005 est :

`(46 096 255,97 − 44 185 561,99) / 44 185 561,99 × 100 = +4,32 %`.

**Interprétation :** après intégration analytique des fichiers refresh, on passe de **−57,48 % apparents** à **+4,32 % calculés**. Le second résultat est cohérent avec les contrôles d'absence de tickets/commandes communs, mais reste **conditionnel** à l'hypothèse que les fichiers refresh sont complémentaires et couvrent les ventes attendues. Une couverture de bornes temporelles ne garantit pas à elle seule une exhaustivité quotidienne.

## 9. Limites, hypothèses et contrôles restant à faire

| Point | Statut | Limite / action recommandée |
|---|---|---|
| Existence des fichiers, nombre de lignes et tailles | **Observé** | Provenance : sorties WSL ; conserver les preuves |
| Nombre de champs | **Partiellement vérifié** | 1re ligne de 23 fichiers ; échantillons de cinq fichiers |
| Champs vides | **Partiellement vérifié** | `item` complet ; quatre autres fichiers sur 1 000 lignes |
| Noms, ordre et types des colonnes des tables principales | **Identifiés dans le DDL officiel v1.7.0** | Compatibilité des nombres de champs observée ; confirmer la version exacte du générateur et vérifier les autres colonnes |
| Relations entre ventes et dimensions | **Cinq relations testées** | Tester aussi les refresh et d'autres tables pertinentes |
| Unicité des clés `item` et `store` | **Testée sur les fichiers initiaux** | Étudier les clés des autres dimensions |
| Granularité des lignes de vente | **Partiellement caractérisée** | 4 136 répétitions de clé candidate, sans doublon complet |
| Mécanisme de `data_refresh` | **Hypothèse de complément** | Formaliser les règles d'ajout/mise à jour par table |
| Montants et quantités | **Calculés** | Devise, taxes, retours, annulations à documenter |
| Couverture temporelle | **Bornes vérifiées pour les ventes** | Vérifier l'exhaustivité par jour et canal |
| Promotions | **Question métier définie seulement** | Identifier les liens et les règles d'analyse, éviter toute conclusion causale |
| Traces de traitements | **À organiser** | Conserver commandes, résultats, scripts et tableaux |

Les valeurs manquantes, les clés de dimension et les répétitions de ventes ne justifient **aucune modification des fichiers sources** sans règle métier établie.

## 10. Synthèse pour préparer l'UC-02

L'exploration révèle un ensemble initial de 23 sources `.dat`, réparties entre les domaines métier du commerce de détail, accompagné d'un ensemble refresh plus petit. Les données présentent des volumes contrastés, notamment pour l'inventaire et les clics web. Les fichiers de ventes permettent déjà de calculer cinq indicateurs décisionnels, mais les résultats exigent une gestion explicite de la qualité, des clés, des actualisations et de la couverture temporelle. L’identification des schémas Hive officiels aide à spécifier les conversions de types et le traitement explicite des champs optionnels, notamment `item.i_rec_end_date`.

Pour la suite, l'architecture devra **préserver les données brutes**, enregistrer leur provenance (source initiale ou refresh), contrôler le schéma et les clés, puis produire des tables analytiques et des KPI reproductibles. Une séparation logique entre zones **Raw/Bronze, Silver et Gold** constitue une option à comparer et à justifier dans l'UC-02 ; il ne s'agit pas d'un déploiement déjà réalisé.

## 11. Preuves et références

### Preuves issues du travail sous WSL

- Dictionnaire technique dérivé de la spécification : fichier joint `UC01_colonnes_types_TPCxBB.csv` (cinq tables).
- Inventaire de répertoires : `ls`, `find`, `du -sh` et `wc -l`.
- Format de `store_sales` : `file`, `head` et `cat -A`.
- Contrôles de structure et complétude : `awk -F'|'` sur échantillons et sur la totalité de `item`.
- Cohérence des clés et doublons : `cut`, `sort -u`, `uniq`, `comm`, `awk`.
- Dates : rapprochement avec `date_dim.dat`.
- Calcul des KPI : agrégations `awk` par canal et par mois.
- Fichiers déjà repérés dans le projet : `inventaire.csv` et dossier `UC01_preuves/` ; l'existence d'autres captures ou justificatifs n'a pas été vérifiée.

### Documentation de référence

- Transaction Processing Performance Council (TPC), **TPCx-BB Standard Specification**, version 1.7.0 : https://www.tpc.org/TPC_Documents_Current_Versions/pdf/TPCX-BB_v1.7.0.pdf
- Annexe I, **définitions `CREATE EXTERNAL TABLE`** : `date_dim` p. 123 ; `item` p. 125 ; `inventory` p. 131 ; `store_sales` p. 132 ; `web_sales` p. 133–134 (numéros de pages imprimés sur le PDF).

**Méthode de vérification :** les montants et volumes sont repris des sorties de terminal fournies ; les additions, moyennes et pourcentages consolidés ont été recalculés. Le rapprochement des schémas DDL officiels avec les fichiers locaux repose sur le nombre de champs et quelques valeurs observées ; il ne constitue pas un contrôle de type sur la totalité de chaque fichier.
