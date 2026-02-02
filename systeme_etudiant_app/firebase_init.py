import firebase_admin
from firebase_admin import credentials, messaging
import os

# Chemin absolu vers le JSON depuis la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
firebase_json_path = os.path.join(BASE_DIR, 'systeme-gestion-etudiant-firebase-adminsdk-fbsvc-cc59976998.json')

# Initialiser Firebase si ce n'est pas déjà fait
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_json_path)
    firebase_admin.initialize_app(cred)
