from pyexpat.errors import messages
from django.contrib.auth import authenticate, login

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout

from django.contrib import messages

from systeme_etudiant_app import backends
from systeme_etudiant_app.backends import EmailBackend
from systeme_etudiant_app.models import CustomUser


# Create your views here.
def showDemoPage(request):
    return render(request,"demo.html")

def ShowLoginPage(request):
    return render(request,"login_page.html")

def doLogin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)

        if user is None:
            try:
                user = CustomUser.objects.get(email=email)
                if user.check_password(password):
                    login(request, user)
                else:
                    raise Exception("Mot de passe invalide")
            except Exception as e:
                messages.error(request, "Email ou mot de passe incorrect")
                return redirect('login_page')

        else:
            login(request, user)

        # Redirection selon le type d'utilisateur
        if user.user_type == 1:
            return redirect('admin_home')
        elif user.user_type == 2:
            return redirect('staff_home')
        elif user.user_type == 3:
            return redirect('student_home')
        else:
            messages.error(request, "Type d'utilisateur inconnu")
            return redirect('login_page')

    return render(request, 'login.html')


def GetUserDetails(request):
    if request.user!=None:
        return HttpResponse("User : "+request.user.email+" usertype : "+request.user.user_type)
    else:
        return HttpResponse("Please login First")
def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")

