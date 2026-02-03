import os
import firebase_admin
from firebase_admin import credentials
from django.conf import settings

# On utilise le BASE_DIR officiel défini dans ton fichier settings.py
# Normalement, c'est C:\Users\HP\Desktop\PROJET
path_to_json = os.path.join(settings.BASE_DIR, 'systeme-gestion-etudiant-firebase-adminsdk-fbsvc-cc59976998.json')

if not firebase_admin._apps:
    if os.path.exists(path_to_json):
        cred = credentials.Certificate(path_to_json)
        firebase_admin.initialize_app(cred)
    else:
        print(f"\n ATTENTION : Fichier manquant à cet endroit précis : {path_to_json}")