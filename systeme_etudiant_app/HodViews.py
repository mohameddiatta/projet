#import json
import re

import unicodedata
#import token
#import traceback

#import requests
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Sum, Q
#from django.http import JsonResponse
from django.utils import timezone
#from google.oauth2 import service_account
#from google.auth.transport.requests import Request
#from .firebase_init import *
#from firebase_admin import messaging
#from idlelib.rpc import request_queue
#from django.template.defaultfilters import first
#from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
#from django.core.mail import message
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from systeme_etudiant_app.models import  FeedBackStudents, FeedBackStaffs, LeaveReportStudent, \
    LeaveReportStaff, Attendance, AttendanceReport, NotificationStudents, NotificationStaffs, Inscription, Filiere, \
    Paiement

from systeme_etudiant_app.models import Courses, CustomUser, Staffs, Subjects, Students, SessionYearModel
from .forms import AddStudentForm, EditStudentForm
from .studentViews import extract_student_info, calculer_frais_inscription


def admin_home(request):
    student_count=Students.objects.all().count()
    staff_count=Staffs.objects.all().count()
    subject_count=Subjects.objects.all().count()
    course_count=Courses.objects.all().count()

    course_all=Courses.objects.all()
    course_name_list=[]
    subject_count_list=[]
    student_count_list_in_course=[]
    for course in course_all:

        subjects=Subjects.objects.filter(course_id=course.id).count()
        students=Students.objects.filter(course_id=course.id).count()
        course_name_list.append(course.course_name)
        subject_count_list.append(subjects)
        student_count_list_in_course.append(students)

    subjects_all=Subjects.objects.all()
    subject_list=[]
    student_count_list_in_subject=[]
    for subject in subjects_all:
        course=Courses.objects.get(id=subject.course_id.id)
        student_counts=Students.objects.filter(course_id=course.id).count()
        subject_list.append(subject.subject_name)
        student_count_list_in_subject.append(student_counts)

    staffs=Staffs.objects.all()
    attendance_present_list_staff=[]
    attendance_absent_list_staff=[]
    staff_name_list=[]
    for staff in staffs:
        subjects_ids=Subjects.objects.filter(staff_id=staff.admin.id)
        attendance=Attendance.objects.filter(subject_id__in=subjects_ids).count()
        leaves=LeaveReportStaff.objects.filter(staff_id=staff.id,leave_status=1).count()
        attendance_present_list_staff.append(attendance)
        attendance_absent_list_staff.append(leaves)
        staff_name_list.append(staff.admin.username)

    students=Students.objects.all()
    attendance_present_list_student=[]
    attendance_absent_list_student=[]
    student_name_list=[]
    for student in students:
        attendance=AttendanceReport.objects.filter(student_id=student.id,status=True).count()
        absent=AttendanceReport.objects.filter(student_id=student.id,status=False).count()
        leaves=LeaveReportStudent.objects.filter(student_id=student.id,leave_status=1).count()
        attendance_present_list_student.append(attendance)
        attendance_absent_list_student.append(leaves+absent)
        student_name_list.append(student.admin.username)
    return render(request, "hod_template/home_content.html",{"student_count":student_count,"staff_count":staff_count,"subject_count":subject_count,"course_count":course_count,"course_name_list":course_name_list,"subject_count_list":subject_count_list,"student_count_list_in_course":student_count_list_in_course,"student_count_list_in_subject":student_count_list_in_subject,"subject_list":subject_list,"attendance_present_list_staff":attendance_present_list_staff,"attendance_absent_list_staff":attendance_absent_list_staff,"staff_name_list":staff_name_list,"attendance_present_list_student":attendance_present_list_student,"attendance_absent_list_student":attendance_absent_list_student,"student_name_list":student_name_list})


def add_staff(request):
    return render(request, "hod_template/add_staff_template.html")


def add_staff_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        address = request.POST.get("address")
        try:
            user = CustomUser.objects.create_user(username=username, password=password, email=email,
                                                  last_name=last_name, first_name=first_name, user_type=2)
            user.staffs.address = address
            user.save()
            messages.success(request, "Successful Added Staff")
            return HttpResponseRedirect(reverse("add_staff"))
        except:
            messages.error(request, "Failed to Added Staff")
            return HttpResponseRedirect(reverse("add_staff"))

def add_student(request):
    form = AddStudentForm()
    return render(request, "hod_template/add_student.html", {"form": form})


def add_student_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")

    form = AddStudentForm(request.POST, request.FILES)

    if form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        email = form.cleaned_data["email"]
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        address = form.cleaned_data["address"]
        session_year_id = form.cleaned_data["session_year_id"]
        course_id = form.cleaned_data["course"]
        sex = form.cleaned_data["sex"]

        # Upload de la photo
        profile_pic = request.FILES.get('profile_pic')
        profile_pic_url = None
        if profile_pic:
            fs = FileSystemStorage()
            filename = fs.save(profile_pic.name, profile_pic)
            profile_pic_url = fs.url(filename)

        try:
            # 1️⃣ Création de l'utilisateur
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                user_type=3
            )

            # 2️⃣ Récupération du cours et de la session
            course_obj = Courses.objects.get(id=course_id)
            session_year = SessionYearModel.objects.get(id=session_year_id)

            # 3️⃣ Création ou mise à jour du profil étudiant
            student, created = Students.objects.update_or_create(
                admin=user,
                defaults={
                    'address': address,
                    'course_id': course_obj,
                    'session_year_id': session_year,
                    'gender': sex,
                    'profile_pic': profile_pic_url
                }
            )

            messages.success(request, "Student added successfully!")
            return HttpResponseRedirect(reverse("add_student"))

        except Exception as e:
            messages.error(request, f"Failed to Add Student: {e}")
            return HttpResponseRedirect(reverse("add_student"))

    else:
        return render(request, "hod_template/add_student.html", {"form": form})

def add_courses(request):
    return render(request, "hod_template/add_courses.html")


def add_courses_save(request):
    if request.method != "POST":
        return HttpResponseRedirect("Method Not Allowed")
    else:
        course = request.POST.get("courses")
        try:
            course_model = Courses(course_name=course)
            course_model.save()
            messages.success(request, "Successful Added Course")
            return HttpResponseRedirect(reverse("add_courses"))
        except:
            messages.error(request, "Failed to Added Course")
            return HttpResponseRedirect(reverse("add_courses"))


def add_subject(request):
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_template/add_subject.html", {"staffs": staffs, "courses": courses})


def add_subject_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        subject_name = request.POST.get("subject_name")
        course_id = request.POST.get("course")
        staff_id = request.POST.get("staff")

        if not subject_name:
            messages.error(request, "Veuillez entrer le nom de la matière")
            return HttpResponseRedirect(reverse("add_subject"))

        try:
            course = Courses.objects.get(id=course_id)
            staff = CustomUser.objects.get(id=staff_id)

            subject = Subjects(subject_name=subject_name, course_id=course, staff_id=staff)
            subject.save()

            messages.success(request, "Successfully Added Subject")
            return HttpResponseRedirect(reverse("add_subject"))

        except Exception as e:
            messages.error(request, f"Failed to Add Subject: {e}")
            return HttpResponseRedirect(reverse("add_subject"))


def normalize_search_term(term):
    """Normaliser le terme de recherche pour ignorer les accents"""
    return unicodedata.normalize('NFKD', term).encode('ASCII', 'ignore').decode('utf-8')


def manage_staff(request):
    # Récupérer tous les membres du personnel
    staffs_list = Staffs.objects.all().select_related('admin')

    # Gestion de la recherche
    search_query = request.GET.get('search', '').strip()

    if search_query:
        # Normaliser le terme de recherche (enlever les accents)
        normalized_search = normalize_search_term(search_query.lower())

        # Créer un Q object pour la recherche
        from django.db.models import Q

        # Chercher dans les champs normalisés
        query = Q()

        # Pour chaque staff, vérifier si le terme de recherche correspond
        for staff in staffs_list:
            # Normaliser les valeurs de chaque champ
            first_name_norm = normalize_search_term(staff.admin.first_name.lower())
            last_name_norm = normalize_search_term(staff.admin.last_name.lower())
            username_norm = normalize_search_term(staff.admin.username.lower())
            email_norm = normalize_search_term(staff.admin.email.lower())
            address_norm = normalize_search_term(staff.address.lower() if staff.address else '')

            # Vérifier si le terme de recherche est contenu dans un des champs
            if (normalized_search in first_name_norm or
                    normalized_search in last_name_norm or
                    normalized_search in username_norm or
                    normalized_search in email_norm or
                    normalized_search in address_norm):
                # Ajouter à la queryset filtrée
                # Note: Cette approche n'est pas optimale pour les grandes bases de données
                pass

        # Alternative: utiliser une approche plus performante avec annotation
        from django.db.models import Value, CharField
        from django.db.models.functions import Concat, Lower

        staffs_list = Staffs.objects.annotate(
            full_name=Concat(
                'admin__first_name', Value(' '), 'admin__last_name',
                output_field=CharField()
            ),
            normalized_full_name=Value('')  # On va filtrer après
        )

        # Filtrer avec icontains (insensible à la casse)
        staffs_list = staffs_list.filter(
            Q(admin__first_name__icontains=search_query) |
            Q(admin__last_name__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(admin__username__icontains=search_query) |
            Q(admin__email__icontains=search_query) |
            Q(address__icontains=search_query)
        )

    # Pagination - 10 éléments par page
    paginator = Paginator(staffs_list, 10)
    page = request.GET.get('page', 1)

    try:
        staffs = paginator.page(page)
    except PageNotAnInteger:
        # Si page n'est pas un entier, afficher la première page
        staffs = paginator.page(1)
    except EmptyPage:
        # Si page est hors limite, afficher la dernière page
        staffs = paginator.page(paginator.num_pages)

    context = {
        'staffs': staffs,
        'search_query': search_query,
    }

    return render(request, "hod_template/manage_staff.html", context)


def manage_student(request):
    search_query = request.GET.get('search', '')

    # DEBUG: Afficher ce qu'on recherche
    print(f"\n=== RECHERCHE: '{search_query}' ===")

    # Base queryset
    if search_query:
        # Filtrer AVEC recherche
        students_list = Students.objects.filter(
            Q(admin__first_name__icontains=search_query) |
            Q(admin__last_name__icontains=search_query) |
            Q(admin__username__icontains=search_query) |
            Q(admin__email__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(course_id__course_name__icontains=search_query)
        ).select_related('admin', 'course_id', 'session_year_id')

        print(f"Mode: RECHERCHE - Filtrage activé")
    else:
        # Sans recherche - tous les étudiants
        students_list = Students.objects.all().select_related('admin', 'course_id', 'session_year_id')
        print(f"Mode: TOUS - Aucun filtre")

    # Tri
    students_list = students_list.order_by('admin__last_name', 'admin__first_name')

    # DEBUG: Afficher les résultats de la recherche
    print(f"Nombre d'étudiants trouvés: {students_list.count()}")
    print("\nRésultats:")
    for student in students_list[:10]:  # Voir les 10 premiers seulement
        print(f"  - {student.admin.first_name} {student.admin.last_name}")

    if students_list.count() > 10:
        print(f"  ... et {students_list.count() - 10} autres")

    print("=" * 50 + "\n")

    # Pagination
    paginator = Paginator(students_list, 20)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)

    context = {
        'students': students,
        'search_query': search_query,
    }

    return render(request, "hod_template/manage_student.html", context)
def manage_course(request):
    courses = Courses.objects.all()
    return render(request, "hod_template/manage_course.html", {"courses": courses})


def manage_subject(request):
    subjects = Subjects.objects.all()
    return render(request, "hod_template/manage_subject.html", {"subjects": subjects})


def edit_staff(request, staff_id):
    staff = Staffs.objects.get(admin=staff_id)
    return render(request, "hod_template/edit_staff_template.html", {"staff": staff, "id": staff_id})


def edit_staff_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        staff_id = request.POST.get("staff_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        address = request.POST.get("address")

        try:

            user = CustomUser.objects.get(id=staff_id)
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = username
            user.address = address
            user.save()

            staff_model = Staffs.objects.get(admin=staff_id)
            staff_model.address = address
            staff_model.save()

            messages.success(request, "Successful Edit Staff")
            return HttpResponseRedirect(reverse("edit_staff",kwargs={"staff_id":staff_id}))
        except:
            messages.error(request, "Failed to Edited Staff")
            return HttpResponseRedirect(reverse("edit_staff",kwargs={"staff_id":staff_id}))


def edit_student(request, student_id):
    request.session['student_id']=student_id
    student = Students.objects.get(admin=student_id)
    form=EditStudentForm()
    form.fields['email'].initial = student.admin.email
    form.fields['first_name'].initial = student.admin.first_name
    form.fields['last_name'].initial = student.admin.last_name
    form.fields['username'].initial = student.admin.username
    form.fields['address'].initial = student.address
    form.fields['course'].initial = student.course_id.id
    form.fields['sex'].initial = student.gender
    form.fields['sex'].initial = student.gender
    form.fields['session_year_id'].initial = student.session_year_id
    return render(request, "hod_template/edit_student_template.html",
                  {"form":form,"id":student_id,"username":student.admin.username})


def edit_student_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid method")
        return HttpResponseRedirect(reverse('manage_student'))

    student_id = request.POST.get('student_id')
    if not student_id:
        messages.error(request, "Student ID is required")
        return HttpResponseRedirect(reverse('manage_student'))

    try:
        student = Students.objects.get(admin=student_id)
    except Students.DoesNotExist:
        messages.error(request, "Student not found")
        return HttpResponseRedirect(reverse('manage_student'))

    form = EditStudentForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']

            # Vérifie les doublons sauf pour l'utilisateur actuel
            if CustomUser.objects.filter(username=username).exclude(id=student.admin.id).exists():
                messages.error(request, f"Le nom d'utilisateur '{username}' est déjà utilisé.")
                return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))

            if CustomUser.objects.filter(email=email).exclude(id=student.admin.id).exists():
                messages.error(request, f"L'email '{email}' est déjà utilisé.")
                return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))

            # Mise à jour de l’utilisateur
            user = student.admin
            user.username = username
            user.email = email
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()

            # Mise à jour de l’étudiant
            student.address = form.cleaned_data['address']
            student.gender = form.cleaned_data['sex']
            student.course_id = Courses.objects.get(id=form.cleaned_data['course'])
            student.session_year_id = SessionYearModel.objects.get(id=form.cleaned_data['session_year_id'])

            # Mise à jour de la photo de profil si changée
            if request.FILES.get('profile_pic'):
                profile_pic = request.FILES['profile_pic']
                fs = FileSystemStorage()
                filename = fs.save(profile_pic.name, profile_pic)
                student.profile_pic = fs.url(filename)

            student.save()

            messages.success(request, "Étudiant modifié avec succès ✅")
            return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))

        except Exception as e:
            messages.error(request, f"Échec de la modification : {e}")
            return HttpResponseRedirect(reverse("edit_student",kwargs={"student_id":student_id}))
    else:
        return render(request, "hod_template/edit_student_template.html",
                      {"form": form, "id": student_id, "username": student.admin.username})

def edit_subject(request, subject_id):
    subject = Subjects.objects.get(id=subject_id)
    course = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_template/edit_subject.html",
                  {"subject": subject, "staffs:": staffs, "course:": course,"id": subject_id})


def edit_subject_save(request, subject_id):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_id = request.POST.get("subject_id")
        subject_name = request.POST.get("subject_name")
        staff_id = request.POST.get("staff")
        course_id = request.POST.get("course")

        try:
            subject = Subjects.objects.get(id=subject_id)
            subject.Subject_name = subject_name
            staff = CustomUser.objects.get(id=staff_id)
            subject.staff_id = staff
            course = CustomUser.objects.get(id=subject_id)
            subject.course_id = course_id,course
            subject.save()

            messages.success(request, "Successfuly Edited Subject")
            return HttpResponseRedirect(reverse("edit_subject",kwargs={"subject":subject_id}))
        except:
            messages.success(request, "Failid to Edit Subject")
            return HttpResponseRedirect(reverse("edit_subject",kwargs={"subject":subject_id}))


def edit_course(request, course_id):
    course = Courses.objects.get(id=course_id)
    return render(request, "hod_templte/edit_course.html", {"course": course, "id": course_id})


def edit_course_save(request, course_id):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        course_id = request.POST.get("course_id")
        course_name = request.POST.get("course")

        try:
            course = Courses.objects.get(id=course_id)
            course.course_name = course_name
            course.save()
            messages.success(request, "Successfuly Edited Course")
            return HttpResponseRedirect(reverse("edit_course",kwargs={"course":course_id}))
        except:
            messages.success(request, "Failid to Edit Course")
            return HttpResponseRedirect(reverse("edit_course",kwargs={"course":course_id}))


def demo_page(request):
    return render(request, "systeme_etudiant_app/demo_page.html")


def manage_session(request):
    return render(request,"hod_template/manage_session_template.html")


def add_session_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("manage_session"))
    else:
        session_start_year=request.POST.get("session_start")
        session_end_year=request.POST.get("session_end")
        try:
            sessionyear=SessionYearModel(session_start_year=session_start_year,session_end_year=session_end_year)
            sessionyear.save()
            messages.success(request, "Successfully Add Session ")
            return HttpResponseRedirect(reverse("manage_session"))
        except:
            messages.success(request, "Failid to Add Session")
            return HttpResponseRedirect(reverse("manage_session"))


@csrf_exempt
def user_email_check(reqest):
    email = reqest.POST.get("email")

    # ⭐ CORRECTION : Vous devez juste utiliser .filter() et non .objects.get.filter()
    user_exists = CustomUser.objects.filter(email=email).exists()

    if user_exists:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


# Fichier : systeme_etudiant_app/HodViews.py

@csrf_exempt
def username_check(request):
    # 1. Récupération de la donnée
    username = request.POST.get("username")


    try:
        user_exists = CustomUser.objects.filter(username=username).exists()

        if user_exists:
            return HttpResponse(True)  # Nom d'utilisateur déjà pris
        else:
            return HttpResponse(False)  # Nom d'utilisateur disponible

    except Exception as e:
        # Gestion des erreurs pour éviter le 500 et envoyer une réponse compréhensible
        print(f"Erreur inattendue lors de la vérification du nom d'utilisateur: {e}")
        return HttpResponse("Error")  # Le JS recevra ceci et affichera "Check failed"


def feedback_message_student(request):
    feedbacks=FeedBackStudents.objects.all()
    return render(request,"hod_template/student_feedback.html",{"feedbacks":feedbacks})


@csrf_exempt
def feedback_message_student_replied(request):
    feedback_id=request.POST.get("id")
    feedback_message=request.POST.get("message")

    try:
       feedback=FeedBackStudents.objects.get(id=feedback_id)
       feedback.feedback_reply=feedback_message
       feedback.save()
       return  HttpResponse("True")
    except FeedBackStudents.DoesNotExist:
        return HttpResponse("False")




def feedback_message_staff(request):
    feedbacks=FeedBackStaffs.objects.all()
    return render(request,"hod_template/staff_feedback.html",{"feedbacks":feedbacks})


@csrf_exempt
def feedback_message_staff_replied(request):
    feedback_id=request.POST.get("id")
    feedback_message=request.POST.get("message")

    try:
       feedback=FeedBackStaffs.objects.get(id=feedback_id)
       feedback.feedback_reply=feedback_message
       feedback.save()
       return  HttpResponse("True")
    except FeedBackStaffs.DoesNotExist:
        return HttpResponse("False")


def student_leave(request):
    leaves=LeaveReportStudent.objects.all()
    return render(request,"hod_template/student_leave.html",{"leaves":leaves})



def student_approve_leave(request, leave_id):
    leave=LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status=1
    leave.save()
    return HttpResponseRedirect(reverse("student_leave"))


def student_disapprove_leave(request, leave_id):
    leave = LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return HttpResponseRedirect(reverse("student_leave"))



def staff_leave(request):
    leaves = LeaveReportStaff.objects.all()
    return render(request, "hod_template/staff_leave.html", {"leaves": leaves})


def staff_approve_leave(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave"))


def staff_disapprove_leave(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave"))

def admin_view_attendance(request):
    subjects = Subjects.objects.all()
    session_year_id = SessionYearModel.objects.all()  # FIX
    return render(request, "hod_template/admin_view_attendance.html", {
        "subjects": subjects,
        "session_year_id": session_year_id
    })


@csrf_exempt
def admin_get_attendance_dates(request):
    try:
        subject = request.POST.get("subject")
        session_year_id = request.POST.get("session_year_id")

        subject_obj = Subjects.objects.get(id=subject)
        session_year_obj = SessionYearModel.objects.get(id=session_year_id)  # FIX

        attendance = Attendance.objects.filter(
            subject_id=subject_obj,
            session_year_id=session_year_obj
        )

        attendance_obj = []
        for a in attendance:
            attendance_obj.append({
                "id": a.id,
                "attendance_date": str(a.attendance_date),
                "session_year_id": a.session_year_id.id
            })

        return JsonResponse(attendance_obj, safe=False)  # FIX : NO json.dumps()

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def admin_get_attendance_student(request):
    try:
        attendance_date = request.POST.get("attendance_date")
        attendance = Attendance.objects.get(id=attendance_date)

        attendance_data = AttendanceReport.objects.filter(attendance_id=attendance)
        list_data = []

        for student in attendance_data:
            data_small = {
                "id": student.student_id.admin.id,
                "name": student.student_id.admin.first_name + " " + student.student_id.admin.last_name,
                "status": student.status
            }
            list_data.append(data_small)

        # SUPPRIMER json.dumps() - JsonResponse le fait automatiquement
        return JsonResponse(list_data, safe=False)

    except Attendance.DoesNotExist:
        return JsonResponse({"error": "Attendance not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Failed to fetch attendance: {str(e)}"}, status=500)


def profile_admin(request):
    user=CustomUser.objects.get(id=request.user.id)
    return render(request,"hod_template/profile_admin.html",{"user":user})


def profile_admin_save(request):
    if request.method!="POST":
        return  HttpResponseRedirect(reverse("profile_admin"))
    else:
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        password=request.POST.get("password")
        try:
            customuser=CustomUser.objects.get(id=request.user.id)
            customuser.first_name=first_name
            customuser.last_name=last_name
            if password!=None and password!="":
                customuser.set_password(password)
            customuser.save()

            messages.success(request, "Successfully Updated Profile ")
            return HttpResponseRedirect(reverse("profile_admin"))
        except:
         messages.success(request, "Failed to Update Profile")
         return HttpResponseRedirect(reverse("profile_admin"))


def admin_send_notification_staff(request):
    staff = Staffs.objects.all()
    return render(request,"hod_template/staff_notification.html", {"staffs": staff})

@csrf_exempt
def admin_send_notification_student(request):
    student=Students.objects.all()
    return  render(request,"hod_template/student_notification.html",{"students":student})



@csrf_exempt
def send_student_notification(request):
    try:
        id = request.POST.get("id")
        message = request.POST.get("message")

        if not id or not id.isdigit():
            return HttpResponse("ID invalide", status=400)

        # Récupération du student via admin_id
        student = Students.objects.get(admin__id=int(id))

        # Création et sauvegarde automatique
        NotificationStudents.objects.create(
            student_id=student,
            message=message
        )

        return HttpResponse("True")

    except Students.DoesNotExist:
        return HttpResponse("student introuvable", status=404)

    except Exception as e:
        return HttpResponse(f"Erreur: {str(e)}", status=500)


@csrf_exempt
def send_staff_notification(request):
    try:
        id = request.POST.get("id")
        message = request.POST.get("message")

        if not id or not id.isdigit():
            return HttpResponse("ID invalide", status=400)

        # Récupération du staff via admin_id
        staff = Staffs.objects.get(admin__id=int(id))

        # Création et sauvegarde automatique
        NotificationStaffs.objects.create(
            staff_id=staff,
            message=message
        )

        return HttpResponse("True")

    except Staffs.DoesNotExist:
        return HttpResponse("Staff introuvable", status=404)

    except Exception as e:
        return HttpResponse(f"Erreur: {str(e)}", status=500)


def get_cleaned_student_info(student):
    """Fonction globale réutilisable pour extraire INE et Téléphone"""
    raw_address = str(student.address) if student.address else ""
    info = {
        'ine': '-',
        'telephone': '-',
        'adresse': raw_address
    }

    if raw_address and raw_address.strip():
        # Extraction INE
        ine_match = re.search(r'(?:INE\s*[:\-]?\s*)?([A-Z]\d{9,13})', raw_address, re.IGNORECASE)
        if ine_match:
            info['ine'] = ine_match.group(1).upper()

        # Extraction Téléphone
        tel_match = re.search(r'(?:Tel|Téléphone)[:\s]*([\d\s\.]{9,})', raw_address, re.IGNORECASE)
        if tel_match:
            info['telephone'] = re.sub(r'\D', '', tel_match.group(1))

    return info


def liste_des_inscrits(request):
    # .all() récupère tout le monde : en_attente, valide, refuse, etc.
    inscriptions = Inscription.objects.select_related(
        'students__admin',
        'filiere',
        'niveau'
    ).order_by('-date_inscription')  # Les plus récents en premier

    students_processed = []

    for ins in inscriptions:
        student = ins.students
        # Utilisation des @property du modèle pour plus de simplicité
        total_paye = ins.montant_paye
        reste = ins.reste_a_payer

        info = {
            'id': student.id,
            'inscription_id': ins.id,
            'full_name': f"{student.admin.first_name} {student.admin.last_name}",
            'email': student.admin.email,
            'filiere': ins.filiere.Nom_filiere if ins.filiere else "-",
            'niveau': ins.niveau.nom_niveau if ins.niveau else "-",
            'statut_inscription': ins.statut,
            'montant_paye': total_paye,
            'reste': reste,
            'pourcentage': ins.pourcentage_paye,
            'ine': '-',
            'telephone': '-',
        }

        # Extraction Regex (INE et Téléphone)
        raw_address = str(student.address) if student.address else ""
        if raw_address:
            # ... ton code regex actuel est correct ...
            ine_match = re.search(r'(?:INE\s*[:\-]?\s*)?([A-Z]\d{9,13})', raw_address, re.IGNORECASE)
            if ine_match: info['ine'] = ine_match.group(1).upper()

            tel_match = re.search(r'(?:Tel|Téléphone)[:\s]*([\d\s\.]{9,})', raw_address, re.IGNORECASE)
            if tel_match: info['telephone'] = re.sub(r'\D', '', tel_match.group(1))

        students_processed.append(info)

    context = {
        'students': students_processed,
        'page_title': 'Gestion Globale des Inscriptions',
    }
    return render(request, "hod_template/liste_des_inscrits.html", context)

from django.http import HttpResponse

from django.core.exceptions import PermissionDenied
@login_required
def student_validation(request):
    if not (request.user.is_superuser or request.user.user_type == '1'):
        raise PermissionDenied("Accès réservé aux administrateurs")

    pending_students = Students.objects.filter(
        status='pending'
    ).select_related(
        'admin',
        'session_year_id'
    ).prefetch_related(
        'inscription_set__documents'  # ← related_name automatique
    )

    return render(request, 'hod_template/validation_inscription.html', {
        'pending_students': pending_students,
        'total_pending': pending_students.count(),
        'page_title': 'Validation des étudiants',
    })


@login_required
def approve_student(request, student_id):
    """Approuver un étudiant - version corrigée"""
    # Même vérification d'accès
    user_type = str(getattr(request.user, 'user_type', ''))
    if user_type != '1' and not request.user.is_superuser:
        messages.error(request, "Accès non autorisé.")
        return redirect('admin_home')

    student = get_object_or_404(Students, id=student_id)

    if request.method == 'POST':
        try:
            student.status = 'approved'
            student.validated_at = timezone.now()
            student.validated_by = request.user
            student.save()

            messages.success(request,
                             f"✅ {student.admin.get_full_name()} approuvé."
                             )
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")

    return redirect('student_validation')


@login_required
def reject_student(request, student_id):
    """Rejeter un étudiant - version corrigée"""
    user_type = str(getattr(request.user, 'user_type', ''))
    if user_type != '1' and not request.user.is_superuser:
        messages.error(request, "Accès non autorisé.")
        return redirect('admin_home')

    student = get_object_or_404(Students, id=student_id)

    if request.method == 'POST':
        try:
            reason = request.POST.get('rejection_reason', '')
            student.status = 'rejected'
            student.rejection_reason = reason
            student.validated_at = timezone.now()
            student.validated_by = request.user
            student.save()

            messages.warning(request,
                             f"❌ {student.admin.get_full_name()} rejeté."
                             )
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")

    return redirect('student_validation')


from django.db.models import F


def regulariser_montants(request):
    inscriptions = Inscription.objects.all()
    count = 0
    for ins in inscriptions:
        # On utilise ta nouvelle fonction de calcul
        nouveau_tarif = calculer_frais_inscription(ins.filiere, ins.niveau)

        # Si le tarif enregistré est différent du tarif réel
        if ins.montant_total != nouveau_tarif:
            ins.montant_total = nouveau_tarif
            ins.save()
            count += 1

    messages.success(request, f"{count} inscriptions ont été mises à jour avec les bons tarifs.")
    return redirect('liste_des_inscrits')


def student_validated_list(request):
    """Affiche la liste des étudiants avec paiement validé"""

    # Filtrer par filière si demandé
    filiere_id = request.GET.get('filiere', 'all')

    # Récupérer toutes les inscriptions complètement payées
    inscriptions_payees = []

    # 1. Récupérer toutes les inscriptions
    toutes_inscriptions = Inscription.objects.all()

    for inscription in toutes_inscriptions:
        # Calculer le total des paiements VALIDÉS
        paiements_valides = Paiement.objects.filter(
            inscription=inscription,
            statut__in=['valide', 'Valide', 'validé', 'payé', 'Payé']
        )
        total_valide = paiements_valides.aggregate(total=Sum('montant'))['total'] or 0

        # Vérifier si complètement payée
        if total_valide >= inscription.montant_total:
            # Filtrer par filière si demandé
            if filiere_id == 'all' or str(inscription.filiere.id) == filiere_id:
                # Récupérer le dernier paiement validé
                dernier_paiement = paiements_valides.order_by('-date_paiement').first()

                inscriptions_payees.append({
                    'student': inscription.students,
                    'inscription': inscription,
                    'paiement': dernier_paiement,
                    'total_valide': total_valide
                })

    # Statistiques
    total_students = Students.objects.filter(status='approved').count()
    pending_count = Students.objects.filter(status='pending').count()

    # Calculer les revenus totaux
    total_revenue = Inscription.objects.aggregate(
        total=Sum('montant_total')
    )['total'] or 0

    # Pagination
    paginator = Paginator(inscriptions_payees, 25)  # 25 par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'students': page_obj,  # Liste paginée
        'total_students': total_students,
        'pending_count': pending_count,
        'total_revenue': total_revenue,
        'filieres': Filiere.objects.all(),
    }

    return render(request, 'hod_template/student_validated_list.html', context)


def paiement_validation(request):
    # On récupère tout, mais on met les "en attente" en premier
    paiements = Paiement.objects.all().select_related('inscription__students__admin').order_by('-date_paiement')
    context = {
        'paiements': paiements
    }
    return render(request, 'hod_template/validation_paiement.html', context)

def detail_inscription(request, inscription_id):
    # 1. Récupération avec optimisation (select_related évite bcp de requêtes SQL)
    inscription = get_object_or_404(
        Inscription.objects.select_related('students__admin', 'filiere', 'niveau'),
        id=inscription_id
    )
    student_obj = inscription.students

    # 2. Extraction des infos (INE, Tel)
    adresse_brute = str(student_obj.address) if student_obj.address else ""
    infos_extraites = extract_student_info(adresse_brute)

    student_processed = {
        'full_name': student_obj.admin.get_full_name(),
        'email': student_obj.admin.email,
        'telephone': infos_extraites.get('telephone', '-'),
        'ine': infos_extraites.get('ine', '-'),
    }

    # 3. Récupération de TOUS les paiements pour le tableau
    paiements = Paiement.objects.filter(inscription=inscription).order_by('-date_paiement')

    # 4. Mise à jour automatique du statut de l'inscription
    # On se base sur la @property pourcentage_paye définie dans ton modèle
    # Dans ton étape 4
    if inscription.pourcentage_paye >= 100 and inscription.statut != 'valide':
        inscription.statut = 'valide'
        inscription.save(update_fields=['statut'])
        inscription.save()

    # 5. Contexte
    context = {
        'inscription': inscription,
        'paiements': paiements,
        'student_processed': student_processed,
        'total_paye': inscription.montant_paye,    # Utilise ta property
        'reste_a_payer': inscription.reste_a_payer, # Utilise ta property
        'pourcentage_paye': inscription.pourcentage_paye,
        # Ajout explicite des documents pour être sûr

    }
    return render(request, 'hod_template/detail_inscription.html', context)




def valider_transaction(request, paiement_id):
    # On autorise si c'est le type '1' OU si c'est le superutilisateur
    user_type = str(getattr(request.user, 'user_type', ''))
    is_admin = (user_type == '1' or request.user.is_superuser)

    if not is_admin:
        messages.error(request, "Accès refusé. Seul l'administrateur peut valider.")
        return redirect('paiement_validation')


    # 2. Récupération sécurisée
    try:
        paiement = Paiement.objects.select_related('inscription').get(id=paiement_id)
        print(f"DEBUG 3 - Paiement trouvé: ID {paiement.id}")
        print(f"DEBUG 4 - Paiement statut avant: '{paiement.statut}'")
        print(f"DEBUG 5 - Paiement montant: {paiement.montant}")
        print(f"DEBUG 6 - Inscription liée: ID {paiement.inscription.id}")
    except Paiement.DoesNotExist:
        print(f"DEBUG 7 - Paiement {paiement_id} non trouvé")
        messages.error(request, f"Paiement #{paiement_id} introuvable.")
        return redirect('liste_des_inscrits')

    # 3. Vérification : si déjà validé, on redirige vers le détail
    if paiement.statut == 'valide':
        messages.warning(request, f"Le paiement {paiement.transaction_id} est déjà validé.")
        print(f"DEBUG 8 - Paiement déjà validé, redirection vers inscription {paiement.inscription.id}")
        return redirect('detail_inscription', inscription_id=paiement.inscription.id)

    # 4. Utilisation d'un bloc 'transaction' pour garantir l'intégrité
    with transaction.atomic():
        # Mise à jour du statut
        ancien_statut = paiement.statut
        paiement.statut = 'valide'
        paiement.save()
        print(f"DEBUG 9 - Statut changé: '{ancien_statut}' → '{paiement.statut}'")

        # Optionnel : Invalider les autres tentatives "en attente"
        echoues = Paiement.objects.filter(
            inscription=paiement.inscription,
            statut='en_attente'
        ).exclude(id=paiement.id).update(statut='echoue')

    messages.success(request,
                     f"Le paiement {paiement.transaction_id} ({paiement.montant} FCFA) a été validé avec succès. "
                     f"Solde restant: {paiement.inscription.reste_a_payer} FCFA"
                     )

    print(f"DEBUG 15 - Redirection vers: detail_inscription/{paiement.inscription.id}/")
    # 5. TOUJOURS rediriger vers le détail de l'inscription
    return redirect('detail_inscription', inscription_id=paiement.inscription.id)


def refuser_transaction(request, paiement_id):
    # 1. Vérification des droits d'accès
    if request.user.user_type == '1':
        # 2. Récupération du paiement
        paiement = get_object_or_404(Paiement, id=paiement_id)

        # 3. On ne refuse que ce qui est encore en attente
        if paiement.statut == 'en_attente':
            paiement.statut = 'refuse'  # Ou 'annule' selon le modèle
            paiement.save()
            messages.info(request, f"La transaction {paiement.transaction_id} a été refusée.")
        else:
            messages.warning(request, "Impossible de refuser une transaction déjà traitée.")

    else:
        messages.error(request, "Accès refusé.")

    return redirect('liste_des_inscrits')


def students_validated(request):
    # On filtre uniquement les étudiants approuvés
    students = Students.objects.filter(status='approved').order_by('-admin__date_joined')

    context = {
        "students": students,
        "total_approved": students.count(),
        "page_title": "Liste des Étudiants Validés"
    }
    return render(request, "hod_template/students_validated.html", context)