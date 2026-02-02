from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class LoginCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        path = request.path.rstrip('/')

        login_urls = [reverse("show_login").rstrip('/'), reverse("do_login").rstrip('/'), reverse("creer_compte_admin").rstrip('/'), reverse("do_creer_compte_admin").rstrip('/'), reverse("creer_compte_staff").rstrip('/'), reverse("do_creer_compte_staff").rstrip('/'), reverse("creer_compte_student").rstrip('/'),reverse("do_creer_compte_student").rstrip('/')]

        # Laisser passer les pages de login
        if path in login_urls:
            return None

        if user.is_authenticated:
            modulename = view_func.__module__

            # --- ADMIN ---
            if user.user_type == 1:
                allowed_modules = ["systeme_etudiant_app.HodViews", "systeme_etudiant_app.views", "django.views.static"]
                if modulename not in allowed_modules:
                    return HttpResponseRedirect(reverse("admin_home"))

            # --- STAFF ---
            elif user.user_type == 2:
                allowed_modules = ["systeme_etudiant_app.staffViews","systeme_etudiant_app.EditResultViewClass", "systeme_etudiant_app.views", "django.views.static"]
                if modulename not in allowed_modules:
                    return HttpResponseRedirect(reverse("staff_home"))

            # --- STUDENT ---
            elif user.user_type == 3:
                allowed_modules = ["systeme_etudiant_app.studentViews", "systeme_etudiant_app.views", "django.views.static"]
                if modulename not in allowed_modules:
                    return HttpResponseRedirect(reverse("student_home"))

            return None  # Tout est ok, continuer la requête normalement

        else:
            # Si non connecté → retour à la page de login
            if path not in login_urls and view_func.__module__ != "django.contrib.auth.views":
                return HttpResponseRedirect(reverse("show_login"))
            return None


# middleware.py
class StudentApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.user.user_type == '3':
            # Exclure certaines URLs
            excluded_paths = [
                '/logout/',
                '/student/waiting-approval/',
                '/student/profile/',
            ]

            if not any(request.path.startswith(path) for path in excluded_paths):
                try:
                    student = request.user.students
                    if student.status != 'approved':
                        from django.shortcuts import redirect
                        return redirect('student_waiting_approval')
                except:
                    pass

        return response