import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate(
    "systeme-gestion-etudiant-firebase-adminsdk-fbsvc-cc59976998.json"
)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
