# Plateforme de Visualisation Statistique

## Description
Cette plateforme permet d'extraire et de visualiser les statistiques d'utilisation des cours depuis une plateforme e-learning, avec une organisation par département.

## Nouvelles Fonctionnalités

### 1. Upload de Fichiers Excel
- **Page de connexion améliorée** : L'utilisateur doit maintenant fournir deux fichiers Excel en plus de ses identifiants
- **Fichier 1** : `departement_cours.xlsx` - Mapping des cours par département
- **Fichier 2** : `utilisateurs_departements.xlsx` - Mapping des utilisateurs par département

### 2. Dashboard par Département
- **Nouvelle page** : `/dashboard` - Visualisation organisée par département
- **Accordéon interactif** : Chaque département a sa propre section
- **Statistiques détaillées** : Cartes avec métriques clés pour chaque département
- **Graphiques séparés** : Utilisateurs et taux de complétion par département
- **Tableaux détaillés** : Liste des cours avec statuts colorés

## Structure des Fichiers Excel Requise

### 1. departement_cours.xlsx
```
| departement | cours        |
|-------------|--------------|
| Informatique| Programmation|
| Informatique| Base de données|
| Maths       | Algèbre      |
| Maths       | Calcul       |
```

### 2. utilisateurs_departements.xlsx
```
| utilisateur      | departement |
|------------------|-------------|
| user1@exemple.com| Informatique|
| user2@exemple.com| Maths       |
| user3@exemple.com| Informatique|
```

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
3. **Extraction des données** : Les données sont extraites de la plateforme e-learning
4. **Visualisation** :
   - **Statistiques globales** : Vue d'ensemble de tous les cours
   - **Dashboard par département** : Vue organisée par département
5. **Export** : Télécharger les données en format Excel

## Fonctionnalités du Dashboard

### Cartes de Statistiques
- **Total Utilisateurs** : Nombre total d'utilisateurs par département
- **Taux de Complétion Moyen** : Moyenne des taux de complétion
- **Nombre de Cours** : Nombre de cours dans le département

### Graphiques
- **Utilisateurs par cours** : Graphique en barres du nombre d'utilisateurs
- **Taux de complétion** : Graphique en barres du taux de complétion

### Tableaux Détaillés
- **Liste des cours** avec métriques individuelles
- **Barres de progression** pour les taux de complétion
- **Statuts colorés** : Excellent (≥80%), Bon (≥60%), Moyen (≥40%), Faible (<40%)

## Navigation
- **Statistiques Globales** : Vue d'ensemble de tous les cours
- **Dashboard Départements** : Vue organisée par département
- **Exporter Excel** : Télécharger les données
- **Déconnexion** : Se déconnecter de l'application

## Structure du Projet
```
mon_projet_stat_web/
├── app/
│   ├── routes.py          # Routes principales (modifié)
│   ├── scraper.py         # Extraction des données
│   ├── templates/
│   │   ├── login.html     # Page de connexion (modifié)
│   │   ├── extract.html   # Statistiques globales (modifié)
│   │   └── dashboard.html # Nouveau dashboard par département
│   └── static/
├── data/                  # Dossier pour les fichiers Excel uploadés
├── run.py
└── requirements.txt
```

## Notes Techniques
- Les fichiers Excel sont automatiquement sauvegardés dans le dossier `data/`
- Le dashboard utilise Bootstrap 5 pour l'interface responsive
- Les graphiques sont générés avec Plotly pour l'interactivité
- L'export Excel inclut les graphiques matplotlib intégrés

## Support
Pour toute question ou problème, vérifiez que :
1. Les fichiers Excel ont la bonne structure
2. Les noms de colonnes correspondent exactement
3. Les données sont au format attendu 