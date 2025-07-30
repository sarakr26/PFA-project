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
            print("\nDonnées après traitement :", file=sys.stderr)
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
        cours_file = request.files.get('cours_file')
        users_file = request.files.get('users_file')
        
        print(f"Tentative de connexion avec username={username}", file=sys.stderr)
        
        if username and password and cours_file and users_file:
            try:
                # Créer le dossier data s'il n'existe pas
                data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
                os.makedirs(data_dir, exist_ok=True)
                
                # Sauvegarder les fichiers Excel
                cours_path = os.path.join(data_dir, 'departement_cours.xlsx')
                users_path = os.path.join(data_dir, 'utilisateurs_departements.xlsx')
                
                cours_file.save(cours_path)
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
            error = "Veuillez remplir tous les champs et déposer les deux fichiers Excel."
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
        return render_template('extract.html', 
                            graph_html=graph_html, 
                            graph_completion_html=graph_completion_html, 
                            data=data, 
                            cours_data_json=json.dumps(data),
                            users_departments=users_departments)
                            
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
            
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500