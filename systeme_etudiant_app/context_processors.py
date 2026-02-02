from .models import Inscription, Students
from .models import Inscription, Students, Paiement


def inscription_id_processor(request):
    """
    Rends l'inscription_id disponible dans tous les templates
    pour que la sidebar puisse générer le lien Paiement.
    """
    if not request.user.is_authenticated:
        return {}
    try:
        student = request.user.students
        inscription = Inscription.objects.filter(student=student).first()
        return {"inscription_id": inscription.id if inscription else None}
    except:
        return {"inscription_id": None}




def admin_pending_count(request):
    context = {}
    if request.user.is_authenticated and hasattr(request.user, 'user_type'):
        if request.user.user_type == '1':  # 1 = Admin
            context['pending_count'] = Students.objects.filter(status='pending').count()
    return context


# context_processors.py
from .models import Inscription, Paiement


def admin_notifications(request):
    """
    Rends les variables de notification disponibles pour tous les templates.
    """
    context = {}
    if request.user.is_authenticated:
        # 1. Pour l'Admin (Nombre de paiements en attente)
        if hasattr(request.user, 'user_type') and request.user.user_type == '1':
            context['pending_count'] = Paiement.objects.filter(statut='en_attente').count()

        # 2. Pour l'Étudiant (ID de son inscription pour le lien paiement)
        elif hasattr(request.user, 'user_type') and request.user.user_type == '3':
            try:
                # Vérifie si ton lien est 'students' ou 'student' dans ton modèle
                student = request.user.students
                inscription = Inscription.objects.filter(students=student).first()
                context['inscription_id'] = inscription.id if inscription else None
            except:
                context['inscription_id'] = None

    return context