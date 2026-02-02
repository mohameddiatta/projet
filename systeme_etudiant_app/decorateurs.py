# student/decorators.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from .models import Students


def student_approved_required(view_func):
    """
    Décorateur qui vérifie que l'étudiant est approuvé par l'administration
    Seuls les étudiants avec status='approved' peuvent accéder
    """

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == '3':  # 3 = Étudiant
            try:
                student = request.user.students
                if student.status != 'approved':
                    # Rediriger vers la page d'attente
                    return redirect('student_waiting_approval')
            except Students.DoesNotExist:
                messages.error(request, "Profil étudiant non trouvé.")
                return redirect('home')
        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    """
    Décorateur pour restreindre l'accès aux administrateurs seulement
    user_type = '1' pour admin
    """

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.user_type != '1':  # 1 = Admin
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('home')

        return view_func(request, *args, **kwargs)

    return wrapper


def staff_required(view_func):
    """
    Décorateur pour restreindre l'accès au staff (admin + autres)
    """

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.user_type not in ['1', '2']:  # 1 = Admin, 2 = Staff
            messages.error(request, "Accès réservé au personnel autorisé.")
            return redirect('home')

        return view_func(request, *args, **kwargs)

    return wrapper