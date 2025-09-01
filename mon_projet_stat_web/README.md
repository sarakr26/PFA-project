# Plateforme de Visualisation Statistique

## Description
Cette plateforme permet d'extraire, d'analyser et de visualiser les statistiques d'utilisation des cours depuis une plateforme e-learning, avec une organisation par département. Elle combine l'automatisation du scraping web et une interface web interactive pour l'exploration des données.

---

## Structure du Projet

```
mon_projet_stat_web/
├── app/
│   ├── routes.py          # Routes principales et logique métier
│   ├── scraper.py         # Extraction automatisée des données (Selenium)
│   ├── scraper.py.new     # Version temporaire du scraper
│   ├── scraper.py.tmp     # Version temporaire du scraper
│   ├── __pycache__/       # Fichiers compilés Python
│   ├── static/
│   │   ├── css/           # Feuilles de style (Bootstrap, personnalisées)
│   │   ├── img/           # Images pour l'interface
│   │   └── js/            # Scripts JavaScript pour l'interactivité
│   └── templates/
│       ├── login.html         # Page de connexion et upload
│       ├── extract.html       # Statistiques globales
│       ├── dashboard.html     # Dashboard par département
│       ├── global_analysis.html # Analyse globale
│       ├── utilisateurs.html  # Liste des utilisateurs
│       ├── utilisateurs_page.html # Détail utilisateur
│       └── cours_sidebar.html # Navigation latérale
├── data/
│   ├── departement_cours.xlsx         # Mapping cours/département
│   ├── utilisateurs_departements.xlsx # Mapping utilisateurs/département
│   └── .gitkeep
├── run.py                 # Point d'entrée de l'application Flask
└── requirements.txt       # Dépendances Python
```

---

## Étapes du Projet

### 1. Web Scraping avec Selenium

- **Objectif** : Automatiser l’extraction des statistiques des cours et des utilisateurs depuis la plateforme e-learning SEBN.
- **Fonctionnement** :
  - Authentification automatique avec Selenium.
  - Navigation vers les pages de cours et d’utilisateurs.
  - Extraction des informations : nom du cours, nombre d’utilisateurs, taux de complétion, statut des utilisateurs.
  - Gestion de la pagination et des exceptions.
  - Sauvegarde des données dans des structures Python pour traitement ultérieur.

### 2. Développement de l’Application Web avec Flask

- **Objectif** : Offrir une interface web pour explorer, filtrer et exporter les statistiques extraites.
- **Fonctionnement** :
  - Authentification sécurisée et upload des fichiers Excel nécessaires.
  - Visualisation des statistiques globales et par département.
  - Filtres dynamiques, graphiques interactifs (Plotly), tableaux détaillés.
  - Export des données et des graphiques au format Excel.
  - Gestion des utilisateurs et des cours par département.

---

## Fonctionnalités Clés

- **Upload de Fichiers Excel** : Mapping des cours et des utilisateurs par département.
- **Dashboard par Département** : Visualisation détaillée et interactive pour chaque département.
- **Statistiques Globales** : Vue d’ensemble de tous les cours.
- **Export Excel** : Téléchargement des statistiques et graphiques.
- **Sécurité** : Authentification et gestion des erreurs.
- **Interface Responsive** : Utilisation de Bootstrap et Plotly.

---

## Structure des Fichiers Excel Requise



###  utilisateurs_departements.xlsx
```
| utilisateur      | departement |
|------------------|-------------|
| user1@exemple.com| Informatique|
| user2@exemple.com| Maths       |
| user3@exemple.com| Informatique|
```

---

## Installation et Utilisation

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancement de l'application
```bash
python run.py
```

### 3. Utilisation
1. **Accéder à l'application** : Ouvrir `http://localhost:5000`
2. **Page de connexion** : 
   - Saisir username et password
   - Déposer le fichier `departement_cours.xlsx`
   - Déposer le fichier `utilisateurs_departements.xlsx`
3. **Extraction des données** : Les données sont extraites automatiquement de la plateforme e-learning.
4. **Visualisation** :
   - **Statistiques globales** : Vue d'ensemble de tous les cours
   - **Dashboard par département** : Vue organisée par département
5. **Export** : Télécharger les données en format Excel

---

## Fonctionnalités du Dashboard

- **Cartes de Statistiques** : Total utilisateurs, taux de complétion moyen, nombre de cours par département.
- **Graphiques** : Utilisateurs par cours, taux de complétion (barres, camemberts).
- **Tableaux Détaillés** : Liste des cours, barres de progression, statuts colorés (Excellent, Bon, Moyen, Faible).
- **Navigation** : Statistiques globales, dashboard départements, export Excel, déconnexion.

---

## Notes Techniques

- Les fichiers Excel sont sauvegardés dans le dossier `data/`.
- Le dashboard utilise Bootstrap 5 pour l’interface responsive.
- Les graphiques sont générés avec Plotly pour l’interactivité.
- L’export Excel inclut les graphiques matplotlib intégrés.
- Les scripts temporaires (`scraper.py.new`, `scraper.py.tmp`) servent au développement et à la sauvegarde intermédiaire.

---

## Support

Pour toute question ou problème, vérifiez que :
1. Les fichiers Excel ont la bonne structure.
2. Les noms de colonnes correspondent exactement.
3. Les données sont au format attendu.

---

## Auteur

Projet réalisé par Krichi Sara.