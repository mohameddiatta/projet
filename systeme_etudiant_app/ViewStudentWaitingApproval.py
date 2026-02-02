# student/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def student_waiting_approval(request):
    """Page d'attente pour les étudiants non approuvés"""
    try:
        student = request.user.students
        context = {
            'student': student,
            'page_title': 'En attente d\'approbation'
        }
        return render(request, 'student_template/waiting_approval.html', context)
    except:
        return redirect('home')

