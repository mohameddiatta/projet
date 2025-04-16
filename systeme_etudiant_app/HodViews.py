import datetime
from django.core.wsgi import get_wsgi_application
from django.template.backends import django



from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render


from systeme_etudiant_app.models import Courses, CustomUser, Staffs, Subjects, Students


def admin_home(request):
     return render(request, "hod_template/home_content.html")
 
def add_staff(request):
    return render(request, "hod_template/add_staff_template.html")

def add_staff_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        email=request.POST.get("email")
        password=request.POST.get("password")
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        username=request.POST.get("username")
        address=request.POST.get("address")
        try:
            user=CustomUser.objects.create_user(username=username,password=password,email=email,last_name=last_name,first_name=first_name,user_type=2)
            user.staffs.address=address
            user.save()
            messages.success(request,"Successful Added Staff")
            return HttpResponseRedirect("/add_staff")
        except:
            messages.error(request,"Failed to Added Staff")
            return HttpResponseRedirect("/add_staff")


def add_student(request):
    return render(request, "hod_template/add_student.html" )

def add_student_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        email=request.POST.get("email")
        password=request.POST.get("password")
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        username=request.POST.get("username")
        address=request.POST.get("address")
        session_start=request.POST.get("session_start")
        session_end=request.POST.get("session_end")
        course_id=request.POST.get("course")
        sex=request.POST.get("sex")
        try:
            user=CustomUser.objects.create_user(username=username,password=password,email=email,last_name=last_name,first_name=first_name,user_type=2)
            user.students.address=address
            course_obj=Courses.objects.get(id=course_id)
            user.students.course_id=course_obj
            user.students.session_start_year=session_start
            user.students.session_end_year=session_end
            user.students.gender=sex
            user.students.profile_pic=""
            user.save()
            messages.success(request,"Successful Added Student")
            return HttpResponseRedirect("/add_student")
        except:
            messages.error(request,"Failed to Added Student")
            return HttpResponseRedirect("/add_student")


def add_course(request):
    return render(request, "hod_template/add_courses.html")

def add_course_save(request):
    if request.method!="POST":
        return HttpResponseRedirect("Method Not Allowed")
    else:
        course=request.POST.get("course")
        try:
           course_model=Courses(course_name=course)
           course_model.save()
           messages.success(request,"Successful Added Course")
           return HttpResponseRedirect("/add_courses")
        except:
            messages.error(request,"Failed to Added Course")
            return HttpResponseRedirect("/add_courses")



def add_subject(request):
    courses=Courses.objects.all()
    staffs=CustomUser.objects.filter(user_type=2)
    return render(request, "hod_template/add_subject.html",{"staffs":staffs,"courses":courses})

def add_subject_save(request):
    if request.method!="POST":
        return HttpResponseRedirect("Method Not Allowed")
    else:
        subject_name=request.POST.get("subject")
        subject_name=request.PST.get("subject_name")
        course_id=request.POST.get("course")
        course=Courses.objects.get(id=course_id)
        staff_id = request.POST.get("staff")
        staff=CustomUser.objects.get("id=staff_id")

        try:
            subject=Subjects(subject_name=subject_name,course_id=course,staff_id=staff)
            subject.save()
            messages.success(request,"Successful Added Subject")
            return HttpResponseRedirect("/add_subject")
        except:
            messages.error(request,"Failed to Added Subject")
            return HttpResponseRedirect("/add_subject")



def manage_staff(request):
    staffs=Staffs.objects.all()
    return render(request, "hod_template/manage_staff.html",{"staffs":staffs})


def manage_student(request):
    students=Students.objects.all()
    return render(request, "hod_template/manage_student.html",{"students":students})

def manage_course(request):
    courses=Courses.objects.all()
    return render(request, "hod_template/manage_course.html",{"courses":courses})

def manage_subject(request):
    subjects=Subjects.objects.all()
    return render(request, "hod_template/manage_subject.html",{"subjects":subjects})


def edit_staff(request,staff_id):
    staff=Staffs.objects.get(admin=staff_id)
    return render(request, "hod_template/edit_staff_template.html",{"staff":staff})


def edit_staff_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        staff_id=request.POST.get("staff_id")
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("fast_name")
        email=request.POST.get("email")
        username=request.POST.get("username")
        address=request.POST.get("address")

        try:

           user=CustomUser.objects.get(id=staff_id)
           user.first_name=first_name
           user.last_name=last_name
           user.email=email
           user.username=username
           user.address=address
           user.save()

           staff_model=Staffs.objects.get(admin=staff_id)
           staff_model.address=address
           staff_model.save()

           messages.success(request, "Successful Edit Stsff")
           return HttpResponseRedirect("/edit_staff/"+staff_id)
        except:
           messages.error(request, "Failed to Edited Staff")
           return HttpResponseRedirect("/edit_staff/"+staff_id)



def edit_student(request,student_id):
    student=Students.objects.get(admin=student_id)
    return render(request, "hod_template/edit_student_template.html",{"student":student})


def edit_student_save(request):
    if request.method!="POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        student_id=request.POST.get("student_id")
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("fast_name")
        email=request.POST.get("email")
        username=request.POST.get("username")
        address=request.POST.get("address")
        session_start = request.POST.get("session_start")
        session_end = request.POST.get("session_end")
        course_id = request.POST.get("course")
        sex = request.POST.get("sex")

        try:

           user=CustomUser.objects.get(id=student_id)
           user.first_name=first_name
           user.last_name=last_name
           user.username=username
           user.email=email
           user.save()

           student=Students.objects.get(admin=student_id)
           student.address = address
           student.session_start_year = session_start
           student.session_end_year = session_end
           student.gender=sex
           course=Courses.objects.get(id=course_id)
           student.course_id=course
           student.save()
           messages.success(request, "Successful Edit Student")
           return HttpResponseRedirect("/edit_student/"+student_id)
        except:
           messages.error(request, "Failed to Edited Staff")
           return HttpResponseRedirect("/edit_student/"+student_id)

def demo_page(request):
    return render(request,"systeme_etudiant_app/demo_page.html")












