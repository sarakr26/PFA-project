from flask import Blueprint, render_template, request, url_for, session, flash, send_file, jsonify, redirect
import plotly.graph_objs as go
import plotly.io as pio
from app.scraper import extract_courses_and_users
import sys
import pandas as pd
import io
import json
import matplotlib.pyplot as plt
import os
import re

bp = Blueprint('main', __name__)

# Données de test simulées
FAKE_USER = {
    'username': 'etudiant',
    'password': '1234'
}
FAKE_NOTES = [
    {'module': 'Mathématiques', 'note': '15.5', 'session': 'Automne'},
    {'module': 'Physique', 'note': '13.0', 'session': 'Automne'},
    {'module': 'Informatique', 'note': '17.0', 'session': 'Automne'},
    {'module': 'Chimie', 'note': '12.5', 'session': 'Printemps'},
    {'module': 'Anglais', 'note': '16.0', 'session': 'Printemps'},
]

def load_department_mappings():
    """Charger les mappings depuis les fichiers Excel uploadés"""
    try:
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        cours_path = os.path.join(data_dir, 'departement_cours.xlsx')
        users_path = os.path.join(data_dir, 'utilisateurs_departements.xlsx')
        
        print(f"Tentative de lecture des fichiers Excel dans {data_dir}", file=sys.stderr)
        
        if not os.path.exists(cours_path) or not os.path.exists(users_path):
            print("Un ou plusieurs fichiers Excel sont manquants", file=sys.stderr)
            return None, None
        
        # Lire le fichier des utilisateurs, spécifiquement la feuille "Effectifs"
        try:
            excel_file = pd.ExcelFile(users_path)
            print(f"Feuilles disponibles : {excel_file.sheet_names}", file=sys.stderr)
            # Lire en utilisant la première ligne comme en-têtes
            user_dept_df = pd.read_excel(users_path, sheet_name='Effectifs', header=1)
            print(f"Colonnes trouvées dans le fichier : {user_dept_df.columns.tolist()}", file=sys.stderr)
            print("\nPremières lignes du fichier :", file=sys.stderr)
            print(user_dept_df.head(), file=sys.stderr)
        except Exception as e:
            print(f"Erreur lors de la lecture de la feuille Effectifs : {str(e)}", file=sys.stderr)
            return None, None
        
        # Vérifier les colonnes nécessaires
        if 'Unnamed: 0' not in user_dept_df.columns or 'Unnamed: 11' not in user_dept_df.columns:
            print(f"Erreur: colonnes manquantes dans le fichier. Colonnes attendues: 'Unnamed: 0', 'Unnamed: 11'", file=sys.stderr)
            print(f"Colonnes trouvées: {user_dept_df.columns.tolist()}", file=sys.stderr)
            return None, None
        
        # Sélectionner et renommer les colonnes
        try:
            user_dept_df = user_dept_df[['Unnamed: 0', 'Unnamed: 11']]
            user_dept_df = user_dept_df.rename(columns={
                'Unnamed: 0': 'matricule',
                'Unnamed: 11': 'departement_actuel'
            })
            # Filtrer les matricules contenant "Trainer"
            user_dept_df = user_dept_df[~user_dept_df['matricule'].astype(str).str.contains('Trainer', case=False)]
            print("\nDonnées après traitement et filtrage des Trainers:", file=sys.stderr)
            print(user_dept_df.head(), file=sys.stderr)
        except Exception as e:
            print(f"Erreur lors du traitement des colonnes : {str(e)}", file=sys.stderr)
            return None, None
        
        # Lire le fichier des cours
        dept_courses_df = pd.read_excel(cours_path)
        
        return dept_courses_df, user_dept_df
    except Exception as e:
        print(f"Erreur lors du chargement des fichiers Excel : {e}", file=sys.stderr)
        return None, None

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users_file = request.files.get('users_file')
        
        print(f"Tentative de connexion avec username={username}", file=sys.stderr)
        
        if username and password and users_file:
            try:
                data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
                os.makedirs(data_dir, exist_ok=True)
                
                # Sauvegarder les fichiers Excel
                cours_path = os.path.join(data_dir, 'departement_cours.xlsx')
                users_path = os.path.join(data_dir, 'utilisateurs_departements.xlsx')
                users_file.save(users_path)
                
                print(f"Fichiers Excel sauvegardés dans {data_dir}", file=sys.stderr)
                
                session['user'] = username
                session['password'] = password
                session['files_uploaded'] = True
                
                print("Redirection vers /extract", file=sys.stderr)
                return redirect(url_for('main.extract'))
            except Exception as e:
                error = f"Erreur lors de la sauvegarde des fichiers : {str(e)}"
                print(f"Erreur lors de la sauvegarde : {e}", file=sys.stderr)
        else:
            error = "Veuillez remplir tous les champs et déposer le fichier Excel des utilisateurs."
            print("Champs manquants ou fichiers non fournis", file=sys.stderr)
    return render_template('login.html', error=error)

@bp.route('/extract', methods=['GET', 'POST'])
def extract():
    print("Début de la route /extract", file=sys.stderr)
    if 'user' not in session or 'password' not in session:
        print("Session utilisateur manquante, redirection vers /login", file=sys.stderr)
        return redirect(url_for('main.login'))
        
    username = session['user']
    password = session['password']
    print(f"Extraction pour user={username}", file=sys.stderr)
    
    try:
        data = extract_courses_and_users(username, password)
        print(f"Résultat extraction : {data}", file=sys.stderr)
        
        if not data:
            flash("Aucune donnée extraite ou identifiants incorrects.", "danger")
            return render_template('extract.html', graph_html=None, graph_completion_html=None, data=None)
        
        # Générer le graphique Plotly pour le nombre d'utilisateurs
        cours = [d['cours'] for d in data]
        users = [d['users'] for d in data]
        fig = go.Figure([go.Bar(x=cours, y=users)])
        fig.update_layout(title="Nombre d'utilisateurs par cours", 
                         xaxis_title="Cours", 
                         yaxis_title="Utilisateurs", 
                         xaxis_tickangle=-45)
        graph_html = pio.to_html(fig, full_html=False)
        
        # Générer le graphique Plotly pour le taux de complétion
        taux = [d['taux_completion'] if isinstance(d['taux_completion'], (int, float)) or 
                (isinstance(d['taux_completion'], str) and d['taux_completion'].replace('.', '', 1).isdigit()) 
                else None for d in data]
        taux = [float(t) if t not in (None, 'N/A') and str(t).replace('.', '', 1).isdigit() 
                else None for t in taux]
        
        fig2 = go.Figure([go.Bar(x=cours, y=taux)])
        fig2.update_layout(title="Taux de complétion (%) par cours", 
                          xaxis_title="Cours", 
                          yaxis_title="Taux de complétion (%)", 
                          xaxis_tickangle=-45)
        graph_completion_html = pio.to_html(fig2, full_html=False)
        
        # Charger les données des utilisateurs et départements
        _, user_dept_df = load_department_mappings()
        if user_dept_df is not None:
            users_departments = user_dept_df.to_dict('records')
            print("\nDonnées envoyées au template :", file=sys.stderr)
            print(f"Nombre d'utilisateurs : {len(users_departments)}", file=sys.stderr)
            print("Premiers utilisateurs :", file=sys.stderr)
            for user in users_departments[:5]:
                print(user, file=sys.stderr)
        else:
            users_departments = []
            print("Aucune donnée d'utilisateurs à envoyer au template", file=sys.stderr)
            flash("Impossible de charger les données des départements", "warning")

        session['last_data'] = data  # Pour export Excel
        # Obtenir la liste unique des départements
        departments = sorted(list(set(user_dept_df['departement_actuel'].dropna().unique())))

        return render_template('extract.html', 
                            graph_html=graph_html, 
                            graph_completion_html=graph_completion_html, 
                            data=data, 
                            cours_data_json=json.dumps(data),
                            users_departments=users_departments,
                            departments=departments,
                            total_rows=len(users_departments) if users_departments else 0)
                            
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erreur lors de l'extraction : {e}\n{tb}", file=sys.stderr)
        flash(f"Erreur lors de l'extraction : {e}", "danger")
        return render_template('extract.html', graph_html=None, graph_completion_html=None, data=None)

@bp.route('/analyze_all_courses', methods=['POST'])
def analyze_all_courses():
    """Route pour analyser tous les cours et leurs utilisateurs par département"""
    if 'user' not in session or 'password' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        # Charger les mappings départementaux
        _, user_dept_df = load_department_mappings()
        if user_dept_df is None:
            return jsonify({'success': False, 'error': 'Impossible de charger les données des départements'})

        # Créer le mapping matricule -> département
        dept_map = {str(row['matricule']).strip(): row['departement_actuel'] 
                   for _, row in user_dept_df.iterrows()}

        # Récupérer la liste des cours
        courses = session.get('last_data', [])
        if not courses:
            return jsonify({'success': False, 'error': 'Aucun cours trouvé'})

        # Pour chaque cours, obtenir les utilisateurs et leurs départements
        courses_analysis = []
        for course in courses:
            if not course.get('lien'):
                continue

            # Extraire l'ID du cours et construire l'URL users
            match = re.search(r'/course/(\d+)', course['lien'])
            if not match:
                continue

            course_id = match.group(1)
            users_url = f'https://elearning.sebn.com/courses/edit/{course_id}/action/users/from-dashboard/1'

            # Extraire les utilisateurs avec fenêtre visible
            from app.scraper import extract_users_from_course
            print(f"[Debug] Extraction des utilisateurs pour le cours {course['cours']}", file=sys.stderr)
            users = extract_users_from_course(session['user'], 
                                           session['password'], 
                                           users_url, 
                                           headless=False)  # Afficher la fenêtre du navigateur

            if users is None:
                continue

            # Compter les utilisateurs par département
            dept_counts = {}
            completed_by_dept = {}
            for user in users:
                mat = str(user.get('matricule', '')).strip()
                dept = dept_map.get(mat, 'Unknown')
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                
                # Track completion status
                if user.get('status', '').upper() == 'COMPLETED':
                    completed_by_dept[dept] = completed_by_dept.get(dept, 0) + 1

            # Calculate completion rates for each department
            dept_completion = {}
            for dept in dept_counts:
                users_in_dept = dept_counts[dept]
                completed = completed_by_dept.get(dept, 0)
                completion_rate = (completed / users_in_dept * 100) if users_in_dept > 0 else 0
                dept_completion[dept] = {
                    'completed': completed,
                    'rate': round(completion_rate, 1)
                }

            course_data = {
                'cours': course['cours'],
                'departments': dept_counts,
                'completion': dept_completion,
                'total': len(users)
            }
            courses_analysis.append(course_data)

        # Sauvegarder l'analyse dans la session
        session['courses_analysis'] = courses_analysis
        session['departments_list'] = sorted(list(set(user_dept_df['departement_actuel'].dropna().unique())))

        return jsonify({'success': True})

    except Exception as e:
        print(f"Erreur lors de l'analyse globale : {str(e)}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/global_analysis')
def global_analysis():
    """Page d'analyse globale des cours"""
    if 'user' not in session:
        return redirect(url_for('main.login'))

    # Récupérer les données e-learning
    data = session.get('last_data', [])
    courses_data = session.get('courses_analysis', [])
    
    # Liste fixe des départements
    departments = ['IT', 'PCP', 'PGM', 'PHR', 'PLM', 'PPE', 'PPM', 'PPR', 'PQM', 'PTS']
    
    # Initialize department statistics
    dept_stats = {}

    # Prepare course data structure from the global analysis table
    global_courses = {}
    if not courses_data:  # If no courses_analysis, try to build from the table data
        courses_data = []
        if data:
            for course in data:
                course_name = course['cours']
                dept_counts = {dept: 0 for dept in departments}
                courses_data.append({
                    'cours': course_name,
                    'departments': dept_counts,
                    'total': course.get('users', 0)
                })

    # Process each department
    for dept in departments:
        dept_courses = []
        total_users = 0
        completed_total = 0
        
        # Go through each course in the global analysis table
        for course in courses_data:
            users_in_dept = course['departments'].get(dept, 0)
            if users_in_dept > 0:  # If this department has users in this course
                # Try to find completion data
                completion_data = next((d for d in data if d['cours'] == course['cours']), None)
                completed = 0
                taux_completion = 0.0
                
                if completion_data:
                    if completion_data.get('completed'):
                        completed = int(completion_data['completed'])
                    if completion_data.get('taux_completion') and completion_data['taux_completion'] != 'N/A':
                        taux_completion = float(completion_data['taux_completion'])
                
                dept_courses.append({
                    'cours': course['cours'],
                    'users': users_in_dept,
                    'completed': completed,
                    'taux_completion': taux_completion
                })
                total_users += users_in_dept
                completed_total += completed
        
        # Calculate average completion rate
        avg_completion = 0.0
        if dept_courses:
            valid_rates = [c['taux_completion'] for c in dept_courses if c['taux_completion'] > 0]
            if valid_rates:
                avg_completion = sum(valid_rates) / len(valid_rates)

        # Store department statistics
        dept_stats[dept] = {
            'courses': dept_courses,
            'total_users': total_users,
            'avg_completion': round(avg_completion, 1),
            'courses_list': [c['cours'] for c in dept_courses]
        }
    
    # Process courses data to get department statistics
    for dept in departments:
        dept_courses = []
        total_users = 0
        
        if courses_data:
            # Get courses for this department from the global analysis table
            for course in courses_data:
                users_in_dept = course['departments'].get(dept, 0)
                if users_in_dept > 0:
                    dept_courses.append({
                        'cours': course['cours'],
                        'users': users_in_dept,
                        'completed': 0,  # We'll update this if available
                        'taux_completion': 0.0  # We'll update this if available
                    })
                    total_users += users_in_dept

            # Try to get completion data from last_data
            if data:
                for course_data in data:
                    course_name = course_data['cours']
                    # Update completion data for matching courses
                    for dept_course in dept_courses:
                        if dept_course['cours'] == course_name:
                            if course_data.get('completed'):
                                dept_course['completed'] = course_data['completed']
                            if course_data.get('taux_completion') and course_data['taux_completion'] != 'N/A':
                                dept_course['taux_completion'] = float(course_data['taux_completion'])

        # Calculate department statistics
        avg_completion = 0.0
        if dept_courses:
            completion_rates = [c['taux_completion'] for c in dept_courses if c['taux_completion'] > 0]
            if completion_rates:
                avg_completion = sum(completion_rates) / len(completion_rates)

        dept_stats[dept] = {
            'courses': dept_courses,
            'total_users': total_users,
            'avg_completion': round(avg_completion, 1),
            'courses_list': [c['cours'] for c in dept_courses]
        }
    
    # Calculer les statistiques par département
    dept_stats = {}
    for dept in departments:
        if dept == 'Département Actuel':
            continue
            
        # Calculer les utilisateurs par cours pour ce département
        dept_courses = []
        total_users = 0
        total_completion = 0
        
        for course in courses_data:
            dept_users = course['departments'].get(dept, 0)
            if dept_users > 0:
                dept_courses.append({
                    'cours': course['cours'],
                    'users': dept_users,
                    'completed': 0,  # We don't have this data yet
                    'taux_completion': 0  # We don't have this data yet
                })
                total_users += dept_users
                
        # Calculate completion rates if we have the data
        if data:  # From last_data
            for course_info in data:
                course_name = course_info.get('cours')
                course_completion = course_info.get('taux_completion', 0)
                for dept_course in dept_courses:
                    if dept_course['cours'] == course_name:
                        dept_course['taux_completion'] = course_completion
                        break

        # Calculate average completion rate
        completed_courses = [c for c in dept_courses if c.get('taux_completion', 0) > 0]
        avg_completion = sum(c['taux_completion'] for c in completed_courses) / len(completed_courses) if completed_courses else 0

        dept_stats[dept] = {
            'courses': dept_courses,
            'total_users': total_users,
            'avg_completion': round(avg_completion, 1),
            'courses_list': [c['cours'] for c in dept_courses]
        }
    
    if not data:
        flash("Aucune donnée disponible. Veuillez d'abord extraire les données.", "danger")
        return redirect(url_for('main.extract'))

    # Liste fixe des départements
    all_departments = ['IT', 'PCP', 'PGM', 'PHR', 'PLM', 'PPE', 'PPM', 'PPR', 'PQM', 'PTS']
    dept_stats = {}
    
    # Charger les données des utilisateurs et départements
    _, user_dept_df = load_department_mappings()
    if user_dept_df is None:
        flash("Impossible de charger les données des départements", "warning")
        return redirect(url_for('main.extract'))

    # Calculer le nombre total d'utilisateurs par département depuis le fichier Excel
    dept_users_count = user_dept_df['departement_actuel'].value_counts().to_dict()
    
    # Pour chaque département, calculer les statistiques
    for dept in all_departments:
        dept_courses = []
        total_weighted_completion = 0
        total_users = dept_users_count.get(dept, 0)
        courses_for_dept = []
        
        for course in data:
            dept_users = [u for u in course.get('users_list', []) 
                         if u.get('departement') == dept]
            
            if dept_users:
                completed = len([u for u in dept_users if u.get('completed', False)])
                users_count = len(dept_users)
                taux = (completed / users_count * 100) if users_count > 0 else 0
                
                dept_courses.append({
                    'cours': course['cours'],
                    'users': users_count,
                    'completed': completed,
                    'taux_completion': round(taux, 2)
                })
                
                courses_for_dept.append(course['cours'])
                total_weighted_completion += taux * users_count
        
        # Calculer la moyenne pondérée du taux de complétion
        avg_completion = (total_weighted_completion / len(dept_courses)) if dept_courses else 0
        
        dept_stats[dept] = {
            'courses': dept_courses,
            'total_users': total_users,
            'avg_completion': round(avg_completion, 2),
            'courses_list': sorted(courses_for_dept)
        }

    # Prepare final data for template
    return render_template('global_analysis.html',
                         courses_data=courses_data,
                         departments=departments,
                         dept_stats=dept_stats)

def extract():
    print("Début de la route /extract", file=sys.stderr)
    if 'user' not in session or 'password' not in session:
        print("Session utilisateur manquante, redirection vers /login", file=sys.stderr)
        return redirect(url_for('main.login'))
        
    username = session['user']
    password = session['password']
    print(f"Extraction pour user={username}", file=sys.stderr)
    
    try:
        data = extract_courses_and_users(username, password)
        print(f"Résultat extraction : {data}", file=sys.stderr)
        
        if not data:
            flash("Aucune donnée extraite ou identifiants incorrects.", "danger")
            return render_template('extract.html', graph_html=None, graph_completion_html=None, data=None)
        
        # Générer le graphique Plotly pour le nombre d'utilisateurs
        cours = [d['cours'] for d in data]
        users = [d['users'] for d in data]
        fig = go.Figure([go.Bar(x=cours, y=users)])
        fig.update_layout(title="Nombre d'utilisateurs par cours", 
                         xaxis_title="Cours", 
                         yaxis_title="Utilisateurs", 
                         xaxis_tickangle=-45)
        graph_html = pio.to_html(fig, full_html=False)
        
        # Générer le graphique Plotly pour le taux de complétion
        taux = [d['taux_completion'] if isinstance(d['taux_completion'], (int, float)) or 
                (isinstance(d['taux_completion'], str) and d['taux_completion'].replace('.', '', 1).isdigit()) 
                else None for d in data]
        taux = [float(t) if t not in (None, 'N/A') and str(t).replace('.', '', 1).isdigit() 
                else None for t in taux]
        
        fig2 = go.Figure([go.Bar(x=cours, y=taux)])
        fig2.update_layout(title="Taux de complétion (%) par cours", 
                          xaxis_title="Cours", 
                          yaxis_title="Taux de complétion (%)", 
                          xaxis_tickangle=-45)
        graph_completion_html = pio.to_html(fig2, full_html=False)
        
        # Charger les données des utilisateurs et départements
        _, user_dept_df = load_department_mappings()
        if user_dept_df is not None:
            users_departments = user_dept_df.to_dict('records')
            print("\nDonnées envoyées au template :", file=sys.stderr)
            print(f"Nombre d'utilisateurs : {len(users_departments)}", file=sys.stderr)
            print("Premiers utilisateurs :", file=sys.stderr)
            for user in users_departments[:5]:
                print(user, file=sys.stderr)
        else:
            users_departments = []
            print("Aucune donnée d'utilisateurs à envoyer au template", file=sys.stderr)
            flash("Impossible de charger les données des départements", "warning")

        session['last_data'] = data  # Pour export Excel
        # Obtenir la liste unique des départements
        departments = sorted(list(set(user_dept_df['departement_actuel'].dropna().unique())))

        return render_template('extract.html', 
                            graph_html=graph_html, 
                            graph_completion_html=graph_completion_html, 
                            data=data, 
                            cours_data_json=json.dumps(data),
                            users_departments=users_departments,
                            departments=departments,
                            total_rows=len(users_departments) if users_departments else 0)
                            
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erreur lors de l'extraction : {e}\n{tb}", file=sys.stderr)
        flash(f"Erreur lors de l'extraction : {e}", "danger")
        return render_template('extract.html', graph_html=None, graph_completion_html=None, data=None)

@bp.route('/dashboard')
def dashboard():
    """Dashboard organisé par département"""
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    # Charger les mappings départementaux
    dept_courses_df, user_dept_df = load_department_mappings()
    
    if dept_courses_df is None or user_dept_df is None:
        flash("Fichiers Excel manquants. Veuillez vous reconnecter avec les fichiers.", "danger")
        return redirect(url_for('main.login'))
    
    # Récupérer les données e-learning
    data = session.get('last_data', [])
    
    if not data:
        flash("Aucune donnée disponible. Veuillez d'abord extraire les données.", "danger")
        return redirect(url_for('main.extract'))
    
    # Organiser les données par département
    dashboard_data = {}
    
    try:
        for dept in dept_courses_df['departement'].unique():
            dept_courses = dept_courses_df[dept_courses_df['departement'] == dept]['cours'].tolist()
            dept_data = [d for d in data if d['cours'] in dept_courses]
            
            if dept_data:  # Seulement afficher les départements avec des données
                # Créer les graphiques pour ce département
                fig_users = go.Figure([go.Bar(
                    x=[d['cours'] for d in dept_data],
                    y=[d['users'] for d in dept_data],
                    marker_color='#4e54c8'
                )])
                fig_users.update_layout(
                    title=f"Utilisateurs par cours - {dept}",
                    xaxis_title="Cours",
                    yaxis_title="Utilisateurs",
                    xaxis_tickangle=-45,
                    height=400.0
                )
                
                # Traitement du taux de complétion
                taux_data = []
                for d in dept_data:
                    taux = d['taux_completion']
                    if isinstance(taux, (int, float)):
                        taux_data.append(float(taux))
                    elif isinstance(taux, str) and taux.replace('.', '', 1).isdigit():
                        taux_data.append(float(taux))
                    else:
                        taux_data.append(0)
                
                fig_completion = go.Figure([go.Bar(
                    x=[d['cours'] for d in dept_data],
                    y=taux_data,
                    marker_color='#43e97b'
                )])
                fig_completion.update_layout(
                    title=f"Taux de complétion (%) - {dept}",
                    xaxis_title="Cours",
                    yaxis_title="Taux de complétion (%)",
                    xaxis_tickangle=-45,
                    height=400.0
                )
                
                dashboard_data[dept] = {
                    'users_graph': pio.to_html(fig_users, full_html=False),
                    'completion_graph': pio.to_html(fig_completion, full_html=False),
                    'courses': dept_data,
                    'total_users': sum(d['users'] for d in dept_data),
                    'avg_completion': sum(taux_data) / len(taux_data) if taux_data else 0
                }
    except Exception as e:
        print(f"Erreur lors de la création du dashboard : {e}", file=sys.stderr)
        flash(f"Erreur lors de la création du dashboard : {e}", "danger")
        return redirect(url_for('main.extract'))
    
    return render_template('dashboard.html', dashboard_data=dashboard_data)

@bp.route('/export_excel')
def export_excel():
    data = session.get('last_data')
    if not data:
        flash("Aucune donnée à exporter.", "danger")
        return redirect(url_for('main.extract'))
        
    df = pd.DataFrame(data)
    output = io.BytesIO()

    # Générer le graphique 1 : Nombre d'utilisateurs par cours
    users = pd.to_numeric(df['users'], errors='coerce')
    plt.figure(figsize=(10, 5))
    plt.bar(df['cours'], users, color='#4e54c8')
    plt.title("Nombre d'utilisateurs par cours")
    plt.xlabel("Cours")
    plt.ylabel("Utilisateurs")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    img1 = io.BytesIO()
    plt.savefig(img1, format='png')
    plt.close()
    img1.seek(0)

    # Générer le graphique 2 : Taux de complétion par cours
    taux = pd.to_numeric(df['taux_completion'], errors='coerce')
    plt.figure(figsize=(10, 5))
    plt.bar(df['cours'], taux, color='#43e97b')
    plt.title("Taux de complétion (%) par cours")
    plt.xlabel("Cours")
    plt.ylabel("Taux de complétion (%)")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    plt.close()
    img2.seek(0)

    # Créer le fichier Excel avec les graphiques
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Statistiques')
        workbook = writer.book
        worksheet = writer.sheets['Statistiques']
        
        # Insérer les images sous le tableau
        row_offset = len(df) + 3
        worksheet.insert_image(row_offset, 0, 'users.png', 
                             {'image_data': img1, 'x_scale': 0.8, 'y_scale': 0.8})
        worksheet.insert_image(row_offset + 22, 0, 'completion.png', 
                             {'image_data': img2, 'x_scale': 0.8, 'y_scale': 0.8})
                             
    output.seek(0)
    return send_file(output, 
                    download_name='statistiques_cours.xlsx', 
                    as_attachment=True, 
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@bp.route('/notes')
def notes():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    return render_template('notes.html', email=session['user'], notes=FAKE_NOTES)

@bp.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('password', None)
    session.pop('files_uploaded', None)
    return redirect(url_for('main.login')) 

@bp.route('/get_enrolled_users', methods=['POST'])
def get_enrolled_users():
    if 'user' not in session or 'password' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.get_json()
    course_url = data.get('course_url')
    if not course_url:
        return jsonify({'error': 'Missing course_url'}), 400
        
    # Extraire l'ID du cours et construire l'URL users
    match = re.search(r'/course/(\d+)', course_url)
    if not match:
        return jsonify({'error': 'Invalid course_url'}), 400
        
    course_id = match.group(1)
    users_url = f'https://elearning.sebn.com/courses/edit/{course_id}/action/users/from-dashboard/1'
    
    from app.scraper import extract_users_from_course
    try:
        users = extract_users_from_course(session['user'], 
                                        session['password'], 
                                        users_url, 
                                        headless=False)
        if users is None:
            return jsonify({'error': 'Scraping failed'}), 500
            
        # Filtrer les utilisateurs qui ont "Trainer" dans leur matricule
        users = [user for user in users if not str(user.get('matricule', '')).lower().__contains__('trainer')]        # Merge department info by matricule
        _, user_dept_df = load_department_mappings()
        dept_map = {}
        if user_dept_df is not None:
            dept_map = {str(row['matricule']).strip(): row['departement_actuel'] for _, row in user_dept_df.iterrows()}

        for u in users:
            mat = str(u.get('matricule', '')).strip()
            u['departement'] = dept_map.get(mat, '')

        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/departments-dashboard')
def departments_dashboard():
    """Dashboard des départements"""
    if 'user' not in session:
        return redirect(url_for('main.login'))

    # Récupérer les données e-learning
    data = session.get('last_data', [])
    
    if not data:
        flash("Aucune donnée disponible. Veuillez d'abord extraire les données.", "danger")
        return redirect(url_for('main.extract'))

    # Liste fixe des départements
    departments = ['IT', 'PCP', 'PGM', 'PHR', 'PLM', 'PPE', 'PPM', 'PPR', 'PQM', 'PTS']
    dept_stats = {}
    
    # Charger les données des utilisateurs et départements
    _, user_dept_df = load_department_mappings()
    if user_dept_df is None:
        flash("Impossible de charger les données des départements", "warning")
        return redirect(url_for('main.extract'))

    # Calculer le nombre total d'utilisateurs par département depuis le fichier Excel
    dept_users_count = user_dept_df['departement_actuel'].value_counts().to_dict()
    
    # Pour chaque département, calculer les statistiques
    for dept in departments:
        dept_courses = []
        total_weighted_completion = 0
        total_users = dept_users_count.get(dept, 0)  # Nombre total d'utilisateurs du département
        courses_for_dept = []
        
        for course in data:
            dept_users = [u for u in course.get('users_list', []) 
                         if u.get('departement') == dept]
            
            if dept_users:  # Si des utilisateurs de ce département sont dans ce cours
                completed = len([u for u in dept_users if u.get('completed', False)])
                users_count = len(dept_users)
                taux = (completed / users_count * 100) if users_count > 0 else 0
                
                dept_courses.append({
                    'cours': course['cours'],
                    'users': users_count,
                    'completed': completed,
                    'taux_completion': round(taux, 2)
                })
                
                courses_for_dept.append(course['cours'])
                total_weighted_completion += taux * users_count
        
        # Calculer la moyenne pondérée du taux de complétion
        avg_completion = (total_weighted_completion / len(dept_courses)) if dept_courses else 0
        
        dept_stats[dept] = {
            'courses': dept_courses,
            'total_users': total_users,  # Nombre total d'utilisateurs du département
            'avg_completion': round(avg_completion, 2),
            'courses_list': sorted(courses_for_dept)  # Liste des cours du département
        }

    return render_template('departments_grid.html',
                         departments=sorted(departments),
                         dept_stats=dept_stats)