from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import sys
import os
import glob
import shutil
import re
import traceback

def extract_users_from_course(username, password, course_url, headless=True):
    """
    Extrait les informations des utilisateurs inscrits à un cours spécifique (toutes les pages)
    """
    print(f"[Selenium] Extraction des utilisateurs pour le cours : {course_url}", file=sys.stderr)
    options = Options()
    options.use_chromium = True
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

    driver = webdriver.Edge(service=Service("C:/WebDriver/msedgedriver.exe"), options=options)
    wait = WebDriverWait(driver, 60)  # timeout augmenté à 60s
    users_data = []

    try:
        # Login
        driver.get("https://elearning.sebn.com/")
        wait.until(EC.presence_of_element_located((By.NAME, "login")))
        driver.find_element(By.NAME, "login").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "submit_login").click()

        # Aller sur le dashboard
        driver.get("https://elearning.sebn.com/start")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ef-course-card")))

        # Extraire l'ID du cours depuis course_url
        import re
        match = re.search(r'/edit/(\d+)/', course_url)
        if match:
            course_id = match.group(1)
        else:
            match = re.search(r'/course/(\d+)', course_url)
            course_id = match.group(1) if match else None

        if course_id:
            # Chercher le lien du cours dans le dashboard et cliquer dessus
            try:
                course_link = driver.find_element(By.CSS_SELECTOR, f'a[href*="/cstart/course/{course_id}"]')
                course_link.click()
                time.sleep(2)  # attendre le chargement
            except Exception as e:
                print(f"[Selenium] Impossible de cliquer sur le cours dans le dashboard : {e}", file=sys.stderr)

        # Aller sur la page users du cours
        driver.get(course_url)

        # Attendre la disparition du loader '.pace' si présent
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.pace')))
        except Exception:
            pass  # Si pas de loader, continuer

        # Sélectionner le nombre maximum de lignes par page
        try:
            rows_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'select.select-rows')))
            options = rows_select.find_elements(By.TAG_NAME, 'option')
            # Prendre la plus grande valeur numérique (ignorer 'show more')
            max_option = max([opt for opt in options if opt.get_attribute('value').isdigit()], key=lambda o: int(o.get_attribute('value')))
            rows_select.click()
            max_option.click()
            time.sleep(2)  # attendre le rechargement
        except Exception as e:
            print(f"[Selenium] Impossible de sélectionner le max de lignes par page : {e}", file=sys.stderr)

        # Pagination : récupérer toutes les pages
        all_users = []
        page_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'select.select-page')))
        page_options = page_select.find_elements(By.TAG_NAME, 'option')
        total_pages = len([opt for opt in page_options if opt.get_attribute('value').isdigit()])
        for i in range(total_pages):
            try:
                # Sélectionner la page i
                page_select = driver.find_element(By.CSS_SELECTOR, 'select.select-page')
                page_options = page_select.find_elements(By.TAG_NAME, 'option')
                page_options[i].click()
                time.sleep(1.5)  # attendre le chargement
                # Attendre que le tableau soit présent
                wait.until(EC.presence_of_element_located((By.ID, "usersTable")))
                user_rows = driver.find_elements(By.CSS_SELECTOR, "#usersTable tr.defaultRowHeight")
                for row in user_rows:
                    try:
                        tds = row.find_elements(By.TAG_NAME, "td")
                        if not tds or len(tds) < 2:
                            continue
                        name_text = tds[0].text.strip()
                        # Vérifier la présence d'un bouton ou input ENROLLED
                        enrolled = False
                        # Vérifier le bouton ENROLLED
                        enrolled_btn = row.find_elements(By.CSS_SELECTOR, "button, .btn, .enrolled")
                        if any('ENROLLED' in btn.text for btn in enrolled_btn):
                            enrolled = True
                        # Vérifier input[value='Enrolled']
                        inputs = row.find_elements(By.CSS_SELECTOR, "input[value='Enrolled']")
                        if inputs:
                            enrolled = True
                        if not enrolled:
                            continue
                        # Extraire nom et matricule
                        if "(MASA" in name_text:
                            name, matricule = name_text.split("(MASA")
                            name = name.strip()
                            matricule = matricule.replace(")", "").strip()
                        else:
                            name = name_text
                            matricule = ""
                        all_users.append({"full_name": name, "matricule": matricule})
                    except Exception as e:
                        print(f"[Selenium] Erreur lors de l'extraction d'un utilisateur: {str(e)}", file=sys.stderr)
                        continue
            except Exception as e:
                print(f"[Selenium] Erreur lors du changement de page {i+1}: {str(e)}", file=sys.stderr)
                continue
        return all_users
    except Exception as e:
        print(f"[Selenium] Erreur lors de l'extraction: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return None
    finally:
        driver.quit()

def extract_courses_and_users(username, password, headless=False):
    """
    Extrait la liste des cours et leurs statistiques
    """
    print("[Selenium] Initialisation du driver Edge", file=sys.stderr)
    options = Options()
    options.use_chromium = True
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
    
    driver = webdriver.Edge(service=Service("C:/WebDriver/msedgedriver.exe"), options=options)
    wait = WebDriverWait(driver, 15)
    results = []
    
    try:
        print("[Selenium] Aller à la page de login", file=sys.stderr)
        driver.get("https://elearning.sebn.com/")
        print("[Selenium] Remplir le formulaire de login", file=sys.stderr)
        wait.until(EC.presence_of_element_located((By.NAME, "login")))
        driver.find_element(By.NAME, "login").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "submit_login").click()
        
        print("[Selenium] Formulaire soumis, attente du dashboard", file=sys.stderr)
        wait.until(EC.url_contains("/start"))
        print("[Selenium] Sur le dashboard, extraction des cours", file=sys.stderr)
        driver.get("https://elearning.sebn.com/start")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ef-course-card")))
        cours_cards = driver.find_elements(By.CSS_SELECTOR, ".ef-course-card")
        print(f"[Selenium] Nombre de cours trouvés : {len(cours_cards)}", file=sys.stderr)
        
        for i, card in enumerate(cours_cards):
            try:
                nom = card.find_element(By.CSS_SELECTOR, "h4 a").text.strip()
                lien = card.find_element(By.CSS_SELECTOR, "h4 a").get_attribute("href")
                print(f"[Selenium] ({i+1}/{len(cours_cards)}) Cours : {nom}", file=sys.stderr)

                result = {
                    'cours': nom,
                    'lien': lien,
                    'users': None,
                    'completed': None,
                    'taux_completion': None
                }

                # Ouvrir le dashboard du cours dans un nouvel onglet
                driver.execute_script("window.open(arguments[0]);", lien)
                driver.switch_to.window(driver.window_handles[-1])
                
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ef-preview-box-course-stats")))
                    stats_boxes = driver.find_elements(By.CSS_SELECTOR, "div.ef-preview-box-course-stats")
                    user_count = None
                    completed_count = None
                    
                    for box in stats_boxes:
                        try:
                            label = box.find_element(By.CSS_SELECTOR, ".ef-info-header").text.strip().lower()
                            value = box.find_element(By.CSS_SELECTOR, ".colored-info").text.strip()
                            if label == "users":
                                user_count = value
                                result['users'] = value
                            elif label == "completed":
                                completed_count = value
                                result['completed'] = value
                        except Exception:
                            continue
                    
                    # Calcul du taux de complétion
                    try:
                        if user_count and completed_count and user_count.isdigit() and completed_count.isdigit():
                            taux = round((int(completed_count) / int(user_count)) * 100, 2)
                            result['taux_completion'] = taux
                        else:
                            result['taux_completion'] = "N/A"
                    except Exception:
                        result['taux_completion'] = "N/A"
                
                except Exception as e:
                    print(f"[Selenium] Erreur lors de l'extraction des statistiques : {str(e)}", file=sys.stderr)
                
                finally:
                    results.append(result)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                
            except Exception as e:
                print(f"[Selenium] Erreur lors de l'extraction du cours : {str(e)}", file=sys.stderr)
                continue
    
    except Exception as e:
        print(f"[Selenium] Erreur générale : {str(e)}", file=sys.stderr)
        return None
    
    finally:
        try:
            driver.quit()
        except:
            pass
    
    return results
