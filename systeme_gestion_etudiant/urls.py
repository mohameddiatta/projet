"""
URL configuration for systeme_gestion_etudiant project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from systeme_etudiant_app import HodViews, views
from systeme_gestion_etudiant import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.ShowLoginPage, name='login_page'),
    path('get_user_details', views.GetUserDetails, name='get_user_details'),
    path('logout', views.logout_user, name='logout'),
    path('logout_user', views.logout_user, name='logout_user'),
    path('admin_home', HodViews.admin_home, name='admin_home'),
    path('demo', views.showDemoPage, name='demo_page'),
    
    path('doLogin', views.doLogin, name='do_login'),
    path('add_staff', HodViews.add_staff, name='add_staff'),
    path('add_staff_save', HodViews.add_staff_save, name='add_staff_save'),
    path('add_student', HodViews.add_student, name='add_student'),
    path('add_student_save', HodViews.add_student_save, name='add_student_save'),
    path('add_courses', HodViews.add_course, name='add_courses'),
    path('add_course_save', HodViews.add_course_save, name='add_course_save'),
    path('add_subject', HodViews.add_subject, name='add_subject'),
    path('add_subject_save', HodViews.add_subject_save, name='add_subject_save'),
    path('manage_staff', HodViews.manage_staff, name='manage_staff'),
    path('manage_student', HodViews.manage_student, name='manage_student'),
    path('manage_courses', HodViews.manage_course, name='manage_courses'),
    path('manage_subject', HodViews.manage_subject, name='manage_subject'),
    path('edit_staff/<str:staff_id>', HodViews.edit_staff, name='edit_staff'),
    path('edit_staff_save', HodViews.edit_staff_save, name='edit_staff_save'),
    path('edit_student/<str:student_id>', HodViews.edit_student, name='edit_student'),
    path('edit_student_save', HodViews.edit_student_save, name='edit_student_save'),
    path('demo_page/', HodViews.demo_page, name='demo_page'),

]

# Ajoute ces lignes en dehors de urlpatterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])