
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.password_validation import password_changed
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from requests import session

from systeme_etudiant_app.models import CustomUser, Students, Courses, SessionYearModel
from .firebase_init import *
from firebase_admin import messaging
import requests


# Create your views here.
def showDemoPage(request):
    return render(request,"demo.html")

def ShowLoginPage(request):
    return render(request,"login_page.html")

#def index2(request):
    #return render(request, "index2.html")


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
import requests


def do_login(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        password = request.POST.get('password')

        # --- Vérification reCAPTCHA v2 ---
        captcha_token = request.POST.get("g-recaptcha-response")
        cap_secret = "6LfTFCMsAAAAANflfvFiedl19023zQ48Pmqk0Lb_"
        cap_url = "https://www.google.com/recaptcha/api/siteverify"

        cap_data = {
            "secret": cap_secret,
            "response": captcha_token
        }

        cap_server_response = requests.post(cap_url, data=cap_data).json()
        if not cap_server_response.get("success"):
            messages.error(request, "Captcha invalide.")
            return redirect("login")

        # --- Authentification ---
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            if user.user_type == 1:
                return redirect("admin_home")
            elif user.user_type == 2:
                return redirect("staff_home")
            elif user.user_type == 3:
                return redirect("student_home")

            messages.error(request, "Type d'utilisateur inconnu.")
            return redirect("login")

        messages.error(request, "Email ou mot de passe incorrect")
        return redirect("login")

    return render(request, "login_page.html")




def GetUserDetails(request):
    if request.user.is_authenticated:
        return HttpResponse("User : "+request.user.email+" usertype : "+request.user.user_type)
    else:
        return HttpResponse("Please login First")


def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")





def showFirebaseJS(request):
    data = """
            importScripts("https://www.gstatic.com/firebasejs/9.0.0/firebase-app.js");
            importScripts("https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging.js");

            // Your web app's Firebase configuration
            var firebaseConfig = {
                apiKey: "AizasDY0TCAvWllTDiNAUKApoGzXpS2yNOO9HMg",
                authDomain: "systeme-gestion-etudiant.firebaseapp.com",
                projectId: "systeme-gestion-etudiant",
                storageBucket: "systeme-gestion-etudiant.appspot.com",
                messagingSenderId: "32960000402",
                appId: "1:32960000402:web:4ea32f6c7e0683bc5aabc6",
                measurementId: "G-4NZNDSKVTQ"
            };

            // Initialize Firebase
            firebase.initializeApp(firebaseConfig);

            // Initialize Firebase Cloud Messaging
            const messaging = firebase.messaging();

            // Background message handler
            messaging.onBackgroundMessage(function(payload) {
                console.log("Message reçu en background :", payload);

                const notificationTitle = payload.notification.title;
                const notificationOptions = {
                    body: payload.notification.body,
                    icon: '/static/images/icon.png'
                };

                return self.registration.showNotification(notificationTitle, notificationOptions);
            });
        """

    return HttpResponse(data)


def creer_compte_admin(request):
    return render(request,"connexion_admin.html")


def creer_compte_staff(request):
    return render(request,"connexion_staff.html")


def creer_compte_student(request):
    courses=Courses.objects.all()
    session_years=SessionYearModel.objects.all()
    return render(request,"connexion_student.html",{"courses":courses,"session_years":session_years})


from django.contrib import messages
from django.shortcuts import render, redirect


def do_creer_compte_admin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # 1. Vérifier si l'utilisateur existe déjà
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
            return render(request,'connexion_staff.html')

        try:
            # 2. Création de l'utilisateur
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                user_type=1
            )
            user.save()
            messages.success(request, "Compte Admin créé avec succès !")
            return render(request,'login_page.html')

        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {e}")

    return render(request, "connexion_admin.html")


def do_creer_compte_staff(request):
    if request.method=='POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        address = request.POST.get('address')
        password = request.POST.get('password')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request,"Ce nom d'utilisateur est deja pris")
            return render(request,"login_page.html")
        try:
            user=CustomUser.objects.create_user(username=username,email=email,password=password,user_type=2)
            user.staffs.address=address
            user.save()
            messages.success(request,"Compte créé avec succès")
            return render(request,'login_page.html')
        except Exception as e:
            messages.error(request,f"Une erreur est survenue : {e}")

    return render(request,"connexion_staff.html")


def do_creer_compte_student(request):
    if request.method=='POST':
            username = request.POST.get("username")
            password = request.POST.get("password")
            email = request.POST.get("email")
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            address = request.POST.get("address")
            session_year_id = request.POST.get("session_year")
            course_id = request.POST.get("course")
            sex = request.POST.get("sex")

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

                messages.success(request, "Compte créé avec succès!")
                return HttpResponseRedirect(reverse("show_login"))

            except Exception as e:
                messages.error(request, f"Une erreur est survenue {e}")
                return HttpResponseRedirect(reverse("creer_compte_student"))


    return render(request, "connexion_staff.html")
