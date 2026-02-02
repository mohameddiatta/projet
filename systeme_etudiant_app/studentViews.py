import os
import re
from datetime import datetime, date
from itertools import count

from _decimal import InvalidOperation, Decimal
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template import context
from django.template.context_processors import request
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from systeme_etudiant_app.models import Subjects, Students, Courses, CustomUser, Attendance, AttendanceReport, \
    LeaveReportStudent, FeedBackStudents, NotificationStudents, StudentResult, SessionYearModel

from django.shortcuts import render, redirect
from django.contrib import messages

from systeme_gestion_etudiant import settings
from . import models
from .forms import CompleteStudentProfileForm
from .models import Inscription, Students, Filiere, Niveau
from django.contrib.auth.decorators import login_required
from .models import Paiement, Inscription
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import logging



@login_required
def student_home(request):
    try:
        student_obj = request.user.students
    except AttributeError: # Utiliser AttributeError si l'accès direct échoue
        messages.error(request, "Profil étudiant non trouvé.")
        return redirect("home")

    # --- LE VERROU DE SÉCURITÉ ---
    # Si l'étudiant n'est pas approuvé, il ne doit PAS voir ses stats
    if student_obj.status != 'approved':
        return redirect('student_waiting_approval')

    # VÉRIFICATION DU COURS
    if student_obj.course_id is None:
        messages.warning(request, "Vous n'avez pas encore de cours assigné.")
        return redirect("student_profile")

    # --- CALCULS DES STATISTIQUES (Votre logique existante) ---
    attendance_total = AttendanceReport.objects.filter(student_id=student_obj).count()
    attendance_present = AttendanceReport.objects.filter(student_id=student_obj, status=True).count()
    attendance_absent = AttendanceReport.objects.filter(student_id=student_obj, status=False).count()

    course = student_obj.course_id
    subjects_count = Subjects.objects.filter(course_id=course).count()

    subject_name = []
    data_present = []
    data_absent = []

    subject_data = Subjects.objects.filter(course_id=course)
    for subject in subject_data:
        attendance = Attendance.objects.filter(subject_id=subject)
        attendance_present_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance, status=True, student_id=student_obj
        ).count()
        attendance_absent_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance, status=False, student_id=student_obj
        ).count()

        subject_name.append(subject.subject_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)

    context = {
        "attendance_total": attendance_total,
        "attendance_absent": attendance_absent,
        "attendance_present": attendance_present,
        "subject": subjects_count,
        "data_name": subject_name,
        "data1": data_present,
        "data2": data_absent,
        "student": student_obj,
    }
    return render(request, "student_template/student_home_template.html", context)

def student_view_attendance(request):
    student = Students.objects.get(admin=request.user.id)
    course =student.course_id
    subjects= Subjects.objects.filter(course_id=course)
    return render(request, "student_template/student_view_attendance.html", {"subjects":subjects})


def student_view_attendance_post(request):
    global attendance_reports
    try:
        subject_id = request.POST.get("subject")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        # Vérifie que les champs sont bien remplis
        if not subject_id or not start_date or not end_date:
            messages.error(request, "Veuillez remplir tous les champs.")
            return render(request, "student_template/student_attendance_data.html")

        # Conversion des dates
        start_date_parse = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_parse = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Récupère les objets liés
        subject_obj = Subjects.objects.get(id=subject_id)
        user_object = CustomUser.objects.get(id=request.user.id)
        stud_obj = Students.objects.get(admin=user_object)

        # ✅ Important : le champ correct dans le modèle est "subject_id", pas "subject"
        attendance_qs = Attendance.objects.filter(
            subject_id=subject_obj,
            attendance_date__range=(start_date_parse, end_date_parse)
        )

        print("Nombre d’attendances filtrées :", attendance_qs.count())

        # Récupère les rapports d'assiduité correspondants
        attendance_reports = AttendanceReport.objects.filter(
            attendance_id__in=attendance_qs,
            student_id=stud_obj
        )

        if not attendance_reports.exists():
            messages.info(request, "Aucun enregistrement trouvé pour cette période.")

        return render(
            request,
            "student_template/student_attendance_data.html",
            {
                "attendance_reports": attendance_reports,
                "subject": subject_obj,
                "start_date": start_date,
                "end_date": end_date,
            }
        )

    except Subjects.DoesNotExist:
        messages.error(request, "La matière sélectionnée est introuvable.")
        return render(request, "student_template/student_attendance_data.html")
    except Exception as e:
        print("Erreur :", e)
        messages.error(request, "Une erreur est survenue lors du filtrage des présences.")
        return render(request, "student_template/student_attendance_data.html",{"attendance_reports":attendance_reports})



def student_apply_leave(request):
    staff_obj = Students.objects.get(admin=request.user.id)
    leave_data = LeaveReportStudent.objects.filter(student_id=staff_obj)
    return render(request, "student_template/student_apply_leave.html", {"leave_data": leave_data})


def student_apply_leave_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_apply_leave"))
    else:
        leave_date = request.POST.get("leave_date")
        leave_msg = request.POST.get("leave_msg")

        student_obj = Students.objects.get(admin=request.user.id)
        try:
            leave_report = LeaveReportStudent(student_id=student_obj, leave_date=leave_date, leave_message=leave_msg,
                                            leave_status=0)
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))
        except:
            messages.error(request, "failed Applied for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))


def student_feedback(request):
    staff_id = Students.objects.get(admin=request.user.id)
    feedback_data = FeedBackStudents.objects.filter(student_id=staff_id)
    return render(request, "student_template/student_feedback.html", {"feedback_data": feedback_data})


def student_feedback_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_feedback"))
    else:
        feedback_msg = request.POST.get("feedback_msg")

        student_obj = Students.objects.get(admin=request.user.id)

        try:
            feedback = FeedBackStudents(student_id=student_obj, feedback=feedback_msg,feedback_reply="")
            feedback.save()
            messages.success(request, "Feedback sent successfully!")
        except Exception as e:
            messages.error(request, f"Failed to send feedback: {str(e)}")

        return redirect("student_feedback")


def profile_student(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Students.objects.get(admin=user)
    return render(request,"staff_template/profile_staff_template.html",{"user":user, "student":student})



def profile_student_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("profile_staff"))
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")
        address = request.POST.get("address")
        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name
            customuser.address = address
            if password != None and password != "":
                customuser.set_password(password)
            customuser.save()

            student=Students.objects.get(admin=customuser)
            student.address=address
            student.save()
            messages.success(request, "Successfully Updated Profile ")
            return HttpResponseRedirect(reverse("profile_staff"))
        except:
            messages.success(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("profile_staff"))



@csrf_exempt
def student_fcmtoken_save(request):
    token = request.POST.get("token")
    try:
        student = Students.objects.get(admin=request.user.id)
        student.fcm_token = token
        student.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")



def student_all_notification(request):
    student=Students.objects.get(admin=request.user.id)
    notifications=NotificationStudents.objects.filter(student_id=student.id)
    return render(request,"student_template/all_notification_student.html",{"notifications":notifications})


def student_result_view(request):
    student=Students.objects.get(admin=request.user.id)
    studentresult=StudentResult.objects.filter(student_id=student.id)
    return render(request,"student_template/result_view_student.html",{"studentresult":studentresult})

logger = logging.getLogger(__name__)


def redirect_to_payment(inscription):
    """Redirection factorisée vers la page de paiement"""
    return redirect('payer_inscription', inscription_id=inscription.id)


@login_required
def complete_profile(request):
    student, created = Students.objects.get_or_create(admin=request.user)

    if request.method == 'POST':
        # N'oublie pas request.FILES pour les fichiers
        form = CompleteStudentProfileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():  # Sécurité : tout passe ou rien ne passe
                    # 1️⃣ Mise à jour de CustomUser
                    request.user.first_name = form.cleaned_data['first_name']
                    request.user.last_name = form.cleaned_data['last_name']
                    request.user.save()

                    # 2️⃣ Mise à jour de Students
                    student.gender = form.cleaned_data['gender']
                    student.address = (
                        f"Adresse : {form.cleaned_data['adresse']} | "
                        f"INE : {form.cleaned_data['numero_ine']} | "
                        f"Téléphone : {form.cleaned_data['telephone']} | "
                        f"Date naissance : {form.cleaned_data['date_naissance']}"
                    )
                    student.status = 'pending'
                    student.rejection_reason = ""
                    student.save()

                    # 3️⃣ Gestion de l’inscription et des fichiers (Plus de table Document)
                    # On récupère ou crée l'inscription
                    inscription, ins_created = Inscription.objects.get_or_create(
                        students=student,
                        # Note : Assure-toi que ton modèle Inscription a un champ 'status'
                        # ou retire cet argument s'il n'existe pas.
                    )

                    # 4️⃣ Enregistrement direct des fichiers dans les champs de l'inscription
                    if 'diplome' in request.FILES:
                        inscription.diplome = request.FILES['diplome']

                    if 'piece_identite' in request.FILES:
                        inscription.piece_identite = request.FILES['piece_identite']

                    if 'photo' in request.FILES:
                        inscription.photo = request.FILES['photo']

                    inscription.save()

                    messages.success(request, "Profil et documents mis à jour avec succès.")
                    return redirect('student_home')

            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
    else:
        # Logique de pré-remplissage inchangée
        extracted = extract_student_info(student.address)  # Correction : passer l'adresse
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'gender': student.gender,
            'adresse': extracted.get('adresse', ''),
            'numero_ine': extracted.get('ine', ''),
            'telephone': extracted.get('telephone', ''),
            'date_naissance': extracted.get('date_naissance', ''),
        }
        form = CompleteStudentProfileForm(initial=initial_data)

    return render(request, 'student_template/inscription_page.html', {
        'form': form,
        'student': student,
        'page_title': 'Compléter mon profil'
    })
@login_required
def student_waiting_approval(request):
    """
    Vue affichée quand l'étudiant n'est pas encore approuvé
    """
    try:
        student = request.user.students
    except AttributeError:
        messages.error(request, "Profil étudiant non trouvé.")
        return redirect("home")

    context = {
        'student_status': student.status,
        'rejection_reason': student.rejection_reason if student.status == 'rejected' else '',
    }

    return render(request, 'student_template/waiting_approval.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

@login_required
def inscription(request):
    try:
        student = request.user.students
    except AttributeError:
        messages.error(request, "Erreur : Profil étudiant non trouvé.")
        return redirect("home")

    # =====================================================
    # 🚫 BLOCAGE TOTAL SI L'ÉTUDIANT N'EST PAS APPROUVÉ
    # =====================================================
    if student.status != 'approved':
        if student.status == 'pending':
            messages.warning(request, "⏳ Votre compte est en attente de validation par l'administration.")
        elif student.status == 'rejected':
            messages.error(request, f"❌ Votre compte a été rejeté : {student.rejection_reason or 'Aucune raison précisée.'}")

        return render(request, "student_template/inscription_page.html", {
            "status_message": "Compte non approuvé",
            "is_disabled": True,
            "profile_complete": False,
            "filieres": [],
            "niveaux": [],
            "inscription": None,
            "inscription_id": None,
            "is_already_registered": False,
            "student_info": {},
            "student": student,
        })

    # =====================================================
    # ✅ PROFIL COMPLET ?
    # =====================================================
    student_info = extract_student_info(student.address)

    profile_complete = all([
        request.user.first_name,
        request.user.last_name,
        request.user.email,
        student_info.get('ine'),
        student_info.get('telephone')
    ])

    # =====================================================
    # 📌 INSCRIPTION EXISTANTE ?
    # =====================================================
    inscription_obj = Inscription.objects.filter(students=student).first()
    is_already_registered = inscription_obj is not None

    # Désactiver formulaire si profil incomplet
    is_disabled = not profile_complete

    # =====================================================
    # 📨 TRAITEMENT DU FORMULAIRE
    # =====================================================
    if request.method == "POST":
        if not profile_complete:
            messages.error(request, "Action refusée : Votre profil est incomplet.")
            return redirect('inscription')

        try:
            with transaction.atomic():
                filiere_id = request.POST.get("filiere")
                niveau_id = request.POST.get("niveau")

                filiere_obj = get_object_or_404(Filiere, ID_filiere=filiere_id)
                niveau_obj = get_object_or_404(Niveau, id=niveau_id)

                frais = calculer_frais_inscription(filiere_obj, niveau_obj)

                inscription_obj, created = Inscription.objects.update_or_create(
                    students=student,
                    defaults={
                        'filiere': filiere_obj,
                        'niveau': niveau_obj,
                        'montant_total': frais
                    }
                )

                # 📂 Upload des documents
                for champ in ["diplome", "releve_notes", "piece_identite", "photo"]:
                    if request.FILES.get(champ):
                        setattr(inscription_obj, champ, request.FILES.get(champ))

                inscription_obj.save()

                # 📊 Vérification dossier
                if inscription_obj.dossier_complet:
                    messages.success(request, "✅ Dossier complet ! Vous pouvez finaliser le paiement.")
                    return redirect('payer_inscription', inscription_id=inscription_obj.id)
                else:
                    messages.warning(
                        request,
                        f"⚠️ Document(s) enregistré(s). Dossier à {inscription_obj.pourcentage_documents:.0f}%."
                    )
                    return redirect('inscription')

        except Exception as e:
            messages.error(request, f"Erreur lors de l'inscription : {str(e)}")
            return redirect('inscription')

    # =====================================================
    # ℹ️ MESSAGE DE STATUT
    # =====================================================
    status_message = None
    if is_already_registered:
        status_message = "✅ Inscription en cours."

    # =====================================================
    # 📦 CONTEXTE TEMPLATE
    # =====================================================
    context = {
        "filieres": Filiere.objects.all(),
        "niveaux": Niveau.objects.all(),
        "profile_complete": profile_complete,
        "student_info": student_info,
        "is_disabled": is_disabled,
        "is_already_registered": is_already_registered,
        "inscription": inscription_obj,
        "inscription_id": inscription_obj.id if inscription_obj else None,
        "status_message": status_message,
        "student": student,
    }

    return render(request, "student_template/inscription_page.html", context)


def calculer_frais_inscription(filiere, niveau):
    code_filiere = str(filiere.ID_filiere).strip().upper()
    nom_niveau = str(niveau.nom_niveau).strip().upper()

    montant = niveau.frais_base

    # 🎓 Cas AP = pas d'augmentation
    if nom_niveau == "AP":
        return montant

    # 🎓 Tous les autres niveaux (Licence, Master…)
    if code_filiere in ["EM", "IG", "AD"]:
        montant += 5000

    return montant


def inscription_status(request):
    # Récupérer l'inscription de l'étudiant si nécessaire
    # inscription = Inscription.objects.filter(students=request.user.students).first()
    context = {
        'message': "Statut de l'inscription (à implémenter)"
        # 'inscription': inscription
    }
    return render(request, 'student_template/inscription_status.html', context)

def structure_address_info(adresse, ine, telephone, date_naissance):
    """Structure les informations dans un format lisible"""
    parts = []
    if adresse and adresse.strip():
        parts.append(f"Adresse: {adresse.strip()}")
    if ine and ine.strip():
        parts.append(f"INE: {ine.strip().upper()}")
    if telephone and telephone.strip():
        parts.append(f"Téléphone: {telephone.strip()}")
    if date_naissance and date_naissance.strip():
        parts.append(f"Date naissance: {date_naissance.strip()}")

    return "\n".join(parts) if parts else ""




# Déplacer ces fonctions utilitaires EN DEHORS de la vue
def extract_student_info(address_text):
    """Extrait les informations structurées du champ address"""
    info = {
        'ine': '',
        'telephone': '',
        'date_naissance': '',
        'adresse': ''
    }

    if not address_text or not address_text.strip():
        return info

    # Diviser par lignes
    lines = address_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if ':' in line:
            try:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                # Détecter le type d'information
                if 'adresse' in key:
                    info['adresse'] = value
                elif key.strip().startswith("ine"):
                    info['ine'] = value
                elif any(word in key for word in ['téléphone', 'telephone', 'tel', 'phone']):
                    info['telephone'] = value
                elif any(word in key for word in ['date', 'naissance', 'birth']):
                    info['date_naissance'] = value
            except Exception as e:
                continue

    # Si certaines infos manquent, essayer de les deviner
    if not info['adresse'] and lines:
        info['adresse'] = lines[0]

    for line in lines:
        line = line.strip()

        # Détecter le numéro INE (1 lettre majuscule + 11 chiffres)
        if not info['ine']:
            ine_match = re.search(r'\b[A-Z][0-9]{11}\b', line.upper())
            if ine_match:
                info['ine'] = ine_match.group(0)  # Ici la correction !!!

        # Détecter le téléphone (10 chiffres commençant par 0 ou format international)
        if not info['telephone']:
            phone_match = re.search(r'(0[1-9][0-9]{8}|\+?\d{8,15})', re.sub(r'\s+', '', line))
            if phone_match:
                info['telephone'] = phone_match.group(1)

        # Détecter la date (YYYY-MM-DD ou DD/MM/YYYY)
        if not info['date_naissance']:
            date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', line)
            if date_match:
                info['date_naissance'] = date_match.group(1)

    return info


def normalize_phone(phone):
    # Supprimer les espaces
    phone = re.sub(r'\s+', '', phone)
    # Ajouter le +221 si le numéro commence par 2 ou 7 et fait 9 chiffres
    if re.match(r'^[27]\d{8}$', phone):
        phone = '+221' + phone
    return phone


@login_required
def student_profile(request):
    """Vue pour compléter et modifier le profil étudiant"""

    # Récupérer ou créer l'étudiant
    try:
        student = request.user.students
    except Students.DoesNotExist:
        # Créer un étudiant si nécessaire
        try:
            session_year = SessionYearModel.objects.first()
            if not session_year:
                messages.error(request, "Aucune année scolaire configurée.")
                return redirect('student_home')

            student = Students.objects.create(
                admin=request.user,
                gender='Male',
                address='',
                session_year_id=session_year,
                fcm_token=''
            )
            messages.info(request, "Profil étudiant créé. Veuillez le compléter.")
        except Exception as e:
            messages.error(request, f"Erreur création profil: {str(e)}")
            return redirect('student_home')

    if request.method == 'POST':
        # Récupérer les données du formulaire
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        gender = request.POST.get('gender', 'Male')
        adresse = request.POST.get('adresse', '').strip()
        numero_ine = request.POST.get('numero_ine', '').strip().upper()
        telephone = request.POST.get('telephone', '').strip()
        date_naissance = request.POST.get('date_naissance', '').strip()
        telephone = normalize_phone(telephone)

        # Validation
        errors = []

        # Validation des champs obligatoires
        if not first_name:
            errors.append("Le prénom est obligatoire.")
        if not last_name:
            errors.append("Le nom est obligatoire.")
        if not email:
            errors.append("L'email est obligatoire.")
        elif '@' not in email:
            errors.append("Email invalide.")

        if not numero_ine:
            errors.append("Le numéro INE est obligatoire.")
        elif not re.match(r'^[A-Z][0-9]{11}$', numero_ine):
            errors.append("Le numéro INE doit commencer par une lettre majuscule suivie de 11 chiffres.")

        if not telephone:
            errors.append("Le téléphone est obligatoire.")

        if not adresse:
            errors.append("L'adresse est obligatoire.")

        if not date_naissance:
            errors.append("La date de naissance est obligatoire.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # 1. Mettre à jour l'utilisateur (CustomUser)
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save()

                # 2. Mettre à jour le modèle Students
                student.gender = gender

                # Structurer et stocker toutes les infos dans le champ address
                student.address = structure_address_info(adresse, numero_ine, telephone, date_naissance)

                # Gérer la photo
                if 'profile_pic' in request.FILES:
                    student.profile_pic = request.FILES['profile_pic']

                student.save()

                messages.success(request, "Votre profil a été mis à jour avec succès !")
                return redirect('student_profile')

            except Exception as e:
                messages.error(request, f"Erreur lors de la sauvegarde: {str(e)}")

    # Extraire les informations existantes pour l'affichage
    student_info = extract_student_info(student.address)

    # Débogage: afficher ce qui est extrait
    print(f"Address raw: {student.address}")
    print(f"Extracted info: {student_info}")

    # Préparer les données pour le formulaire
    initial_data = {
        'first_name': request.user.first_name or '',
        'last_name': request.user.last_name or '',
        'email': request.user.email or '',
        'gender': student.gender or 'Male',
        'adresse': student_info['adresse'] or '',
        'numero_ine': student_info['ine'] or '',
        'telephone': student_info['telephone'] or '',
        'date_naissance': student_info['date_naissance'] or '',
    }

    context = {
        'student': student,
        'student_info': student_info,
        'initial_data': initial_data,
        'page_title': 'Mon Profil',
        'user': request.user,
    }

    # IMPORTANT: Toujours retourner une réponse
    return render(request, 'student_template/student_profile.html', context)


@login_required
def payer_inscription(request, inscription_id):
    student = get_object_or_404(Students, admin=request.user)
    inscription = get_object_or_404(Inscription, id=inscription_id, students=student)

    # Calcul des montants
    montant_valide = Paiement.objects.filter(
        inscription=inscription,
        statut='valide'
    ).aggregate(total=Sum('montant'))['total'] or 0
    reste_a_payer = inscription.montant_total - montant_valide

    context = {
        'inscription': inscription,
        'paiements': Paiement.objects.filter(inscription=inscription).order_by('-date_paiement'),
        'methodes_paiement': Paiement.METHODES_PAIEMENT,
        'montant_valide': montant_valide,
        'reste_a_payer': reste_a_payer,
        'page_title': 'Paiement Inscription'
    }
    return render(request, 'student_template/page_paiement.html', context)

def save_payment(request, inscription_id):
    if request.method == "POST":
        inscription = get_object_or_404(Inscription, id=inscription_id)

        # Récupération des données du formulaire
        montant = request.POST.get('montant')
        methode = request.POST.get('methode')
        transaction_id = request.POST.get('transaction_id')

        # RÉCUPÉRATION DU FICHIER (Image du reçu)
        recu_file = request.FILES.get('recu')

        try:
            # Création du paiement
            paiement = Paiement(
                inscription=inscription,
                montant=montant,
                methode=methode,
                transaction_id=transaction_id,
                recu=recu_file,  # Le fichier est stocké ici
                statut='en_attente'  # Toujours en attente au début
            )
            paiement.save()

            messages.success(request,
                             "Votre preuve de paiement a été envoyée. Elle sera vérifiée par l'administration.")
            return redirect('payer_inscription', inscription_id=inscription.id)

        except Exception as e:
            messages.error(request, f"Erreur lors de l'envoi : {e}")
            return redirect('payer_inscription', inscription_id=inscription.id)


@login_required
def generer_recu_pdf(request, paiement_id):
    paiement = get_object_or_404(Paiement, id=paiement_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Recu_{paiement.transaction_id}.pdf"'

    p = canvas.Canvas(response, pagesize=A5)
    width, height = A5

    # --- AJOUT DU LOGO ---
    # On récupère le chemin physique de l'image dans votre dossier static
    logo_path = os.path.join(settings.BASE_DIR, 'static/images/logo.png')

    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        # drawImage(image, x, y, width, height, mask)
        p.drawImage(logo, 1 * cm, height - 2.5 * cm, width=2 * cm, height=2 * cm, preserveAspectRatio=True, mask='auto')

    # --- ENTÊTE DE L'ÉTABLISSEMENT ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(3.5 * cm, height - 1.5 * cm, "UCAB DE DAKAR")
    p.setFont("Helvetica", 8)
    p.drawString(3.5 * cm, height - 2 * cm, "Service de la Scolarité / Bureau des Finances")
    p.drawString(3.5 * cm, height - 2.4 * cm, "Contact : +221 77 076 15 40 | Email : diattas994@gmail.com")

    # --- TITRE DU REÇU ---
    p.line(1 * cm, height - 3 * cm, width - 1 * cm, height - 3 * cm)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 4 * cm, "REÇU DE PAIEMENT")

    # Numéro du reçu
    p.setFont("Helvetica", 10)
    annee = paiement.date_paiement.strftime('%Y')
    p.drawRightString(width - 1 * cm, height - 4.5 * cm, f"N° : {paiement.id}/{annee}")
    # --- INFOS ÉTUDIANT ---
    p.setFont("Helvetica-Bold", 11)
    p.drawString(1.5 * cm, height - 6 * cm, "INFORMATIONS DE L'ÉTUDIANT")
    p.line(1.5 * cm, height - 6.2 * cm, 7 * cm, height - 6.2 * cm)

    p.setFont("Helvetica", 10)
    p.drawString(1.5 * cm, height - 7 * cm, f"Nom complet : {request.user.get_full_name().upper()}")
    p.drawString(1.5 * cm, height - 7.6 * cm, f"Filière : {paiement.inscription.filiere.get_Nom_filiere_display()}")
    p.drawString(1.5 * cm, height - 8.2 * cm, f"Niveau : {paiement.inscription.niveau.nom_niveau}")

    # --- DÉTAILS DU RÈGLEMENT ---
    p.setFillColorRGB(0.95, 0.95, 0.95)  # Gris clair pour le fond du tableau
    p.rect(1 * cm, height - 12 * cm, width - 2 * cm, 3 * cm, fill=1)

    p.setFillColorRGB(0, 0, 0)  # Retour au noir pour le texte
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1.5 * cm, height - 10 * cm, "Détails de la transaction")
    p.setFont("Helvetica", 10)
    p.drawString(1.5 * cm, height - 10.7 * cm, f"Référence : {paiement.transaction_id}")
    p.drawString(1.5 * cm, height - 11.4 * cm, f"Mode de paiement : {paiement.get_methode_display()}")

    # --- MONTANT ---
    p.setFont("Helvetica-Bold", 14)
    p.drawRightString(width - 1.5 * cm, height - 11.4 * cm, f"TOTAL : {paiement.montant} FCFA")

    # --- PIED DE PAGE ---
    p.line(1 * cm, 2 * cm, width - 1 * cm, 2 * cm)
    p.setFont("Helvetica-Oblique", 7)
    p.drawCentredString(width / 2, 1.5 * cm,
                        "Ce reçu est généré automatiquement et sert de preuve officielle de versement.")
    p.drawCentredString(width / 2, 1.2 * cm, "Toute falsification expose son auteur à des sanctions disciplinaires.")
    # --- Emplacement Signature/Cachet ---
    p.setFont("Helvetica-Bold", 9)
    p.drawString(width - 5 * cm, 4 * cm, "Le Comptable")
    p.setDash(1, 2)  # Ligne pointillée
    p.line(width - 5 * cm, 2.5 * cm, width - 1.5 * cm, 2.5 * cm)

    p.showPage()
    p.save()
    return response


def mes_inscriptions(request):
    """Affiche les inscriptions de l'étudiant connecté"""
    try:
        student = Students.objects.get(admin=request.user)

        # Récupérer toutes les inscriptions
        inscriptions = Inscription.objects.filter(students=student).order_by('-date_inscription')

        # Préparer les données pour le template
        inscriptions_data = []
        for ins in inscriptions:
            inscriptions_data.append({
                'inscription': ins,
                'montant_valide': ins.montant_paye,
                'reste_a_payer': ins.reste_a_payer,
                'pourcentage': ins.pourcentage_paye,
                'paiements': ins.paiement_set.all().order_by('-date_paiement'),

                # Utilisation de la propriété liste_documents
                'documents': ins.liste_documents,  # CECI DOIT EXISTER DANS LE MODÈLE

                # Informations supplémentaires utiles
                'documents_presents': ins.documents_presents,
                'documents_manquants': ins.documents_manquants,
                'nombre_documents': ins.nombre_documents,
                'nombre_documents_presents': ins.nombre_documents_presents,
                'pourcentage_documents': ins.pourcentage_documents,
                'dossier_complet': ins.dossier_complet,
            })

        context = {
            'inscriptions_data': inscriptions_data,
            'student': student,
        }

        return render(request, 'student_template/mes_inscriptions.html', context)

    except Students.DoesNotExist:
        messages.error(request, "Étudiant non trouvé.")
        return redirect('student_home')

@login_required
def student_waiting_approval(request):
    # On récupère l'étudiant lié à l'utilisateur connecté
    try:
        student = request.user.students
    except AttributeError:
        # Au cas où un admin essaierait d'accéder à cette page
        messages.error(request, "Accès réservé aux comptes étudiants.")
        return redirect("admin_home")

    # Si par hasard l'étudiant est déjà approuvé et tente d'accéder à cette page
    if student.status == 'approved':
        return redirect('student_home')

    context = {
        "student": student,
        "page_title": "Statut de votre compte"
    }
    return render(request, "student_template/waiting_approval.html", context)

@login_required
def effectuer_paiement(request, inscription_id):
    student = request.user.students
    inscription = get_object_or_404(Inscription, id=inscription_id, students=student)

    # Calcul du montant restant pour contrôle
    montant_valide = Paiement.objects.filter(inscription=inscription, statut='valide').aggregate(total=Sum('montant'))['total'] or 0
    reste_a_payer = inscription.montant_total - montant_valide

    if request.method == 'POST':
        # 1. Récupération des données du formulaire
        montant_saisi = request.POST.get('montant')
        methode = request.POST.get('methode')
        transaction_id = request.POST.get('transaction_id')
        photo_recu = request.FILES.get('recu') # Récupère l'image de la preuve

        # 2. Sauvegarde du paiement
        Paiement.objects.create(
            inscription=inscription,
            montant=montant_saisi,
            methode=methode,
            transaction_id=transaction_id,
            recu=photo_recu,
            statut='en_attente' # Statut par défaut
        )

        # 3. Message de succès et redirection vers l'historique
        messages.success(request, f"Votre preuve de paiement de {montant_saisi} FCFA a été envoyée avec succès !")
        return redirect('payer_inscription', inscription_id=inscription.id)

    context = {
        'inscription': inscription,
        'reste_a_payer': reste_a_payer,
        'methodes_paiement': Paiement.METHODES_PAIEMENT,
    }
    return render(request, 'student_template/effctuer_paiement.html', context)


from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Inscription, Students


@login_required
def dossier_detail_student(request, inscription_id):
    """Affiche les détails d'une inscription pour l'étudiant"""
    try:
        student = Students.objects.get(admin=request.user)
        inscription = get_object_or_404(Inscription, id=inscription_id, students=student)

        # Vérifier que l'inscription appartient bien à l'étudiant connecté
        if inscription.students != student:
            from django.contrib import messages
            messages.error(request, "Accès non autorisé.")
            return redirect('mes_inscriptions')

        # Calculer le pourcentage de paiement
        pourcentage_paye = 0
        if inscription.montant_total > 0:
            pourcentage_paye = (inscription.montant_paye / inscription.montant_total) * 100

        # Pourcentage de documents
        total_docs = 4
        docs_presents = sum([
            1 if inscription.diplome else 0,
            1 if inscription.releve_notes else 0,
            1 if inscription.piece_identite else 0,
            1 if inscription.photo else 0
        ])
        pourcentage_docs = (docs_presents / total_docs) * 100 if total_docs > 0 else 0

        context = {
            'inscription': inscription,
            'student': student,
            'paiements': inscription.paiement_set.all().order_by('-date_paiement'),
            'total_paye': inscription.montant_paye,
            'reste_a_payer': inscription.reste_a_payer,
            'pourcentage_paye': pourcentage_paye,
            'pourcentage_docs': pourcentage_docs,
            'docs_presents': docs_presents,
            'total_docs': total_docs,
            'documents': [
                {'nom': 'Diplôme', 'present': bool(inscription.diplome),
                 'url': inscription.diplome.url if inscription.diplome else None},
                {'nom': 'Relevé', 'present': bool(inscription.releve_notes),
                 'url': inscription.releve_notes.url if inscription.releve_notes else None},
                {'nom': 'CNI', 'present': bool(inscription.piece_identite),
                 'url': inscription.piece_identite.url if inscription.piece_identite else None},
                {'nom': 'Photo', 'present': bool(inscription.photo),
                 'url': inscription.photo.url if inscription.photo else None},
            ]
        }

        return render(request, 'student_template/dossier_detail_student.html', context)

    except Students.DoesNotExist:
        from django.contrib import messages
        messages.error(request, "Étudiant non trouvé.")
        return redirect('student_home')


@login_required
def mis_ajour_document(request, inscription_id):
    """Permet à l'étudiant de mettre à jour ses documents"""
    try:
        student = request.user.students
        inscription = get_object_or_404(Inscription, id=inscription_id, students=student)

        # Vérifier que l'étudiant peut modifier (statut rejeté ou en attente)
        if inscription.statut == 'approuvé':
            messages.error(request, "Votre inscription est déjà approuvée, vous ne pouvez plus modifier les documents.")
            return redirect('dossier_detail', inscription_id=inscription.id)

        if request.method == "POST":
            try:
                with transaction.atomic():
                    # Mettre à jour seulement les fichiers fournis
                    if 'diplome' in request.FILES:
                        inscription.diplome = request.FILES['diplome']
                        messages.info(request, "Diplôme mis à jour avec succès.")

                    if 'releve_notes' in request.FILES:
                        inscription.releve_notes = request.FILES['releve_notes']
                        messages.info(request, "Relevé de notes mis à jour avec succès.")

                    if 'piece_identite' in request.FILES:
                        inscription.piece_identite = request.FILES['piece_identite']
                        messages.info(request, "Pièce d'identité mise à jour avec succès.")

                    if 'photo' in request.FILES:
                        inscription.photo = request.FILES['photo']
                        messages.info(request, "Photo mise à jour avec succès.")

                    # Réinitialiser le statut à "en attente" si c'était "rejeté"
                    if inscription.statut == 'rejeté':
                        inscription.statut = 'en attente'
                        inscription.motif_rejet = None

                    inscription.save()

                    messages.success(request, "Documents mis à jour avec succès ! Votre dossier sera réexaminé.")
                    return redirect('dossier_detail', inscription_id=inscription.id)

            except Exception as e:
                messages.error(request, f"Erreur lors de la mise à jour : {str(e)}")

        # Contexte pour le template
        documents_info = [
            {
                'nom': 'Diplôme ou Attestation',
                'nom_champ': 'diplome',
                'fichier': inscription.diplome,
                'present': bool(inscription.diplome)
            },
            {
                'nom': 'Relevé de notes',
                'nom_champ': 'releve_notes',
                'fichier': inscription.releve_notes,
                'present': bool(inscription.releve_notes)
            },
            {
                'nom': 'Pièce d\'identité',
                'nom_champ': 'piece_identite',
                'fichier': inscription.piece_identite,
                'present': bool(inscription.piece_identite)
            },
            {
                'nom': 'Photo d\'identité',
                'nom_champ': 'photo',
                'fichier': inscription.photo,
                'present': bool(inscription.photo)
            }
        ]

        context = {
            'inscription': inscription,
            'documents': documents_info,
            'page_title': 'Mettre à jour mes documents'
        }

        return render(request, 'student_template/mis_a_jours_document.html', context)

    except Exception as e:
        messages.error(request, f"Erreur : {str(e)}")
        return redirect('mes_inscriptions')