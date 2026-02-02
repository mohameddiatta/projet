from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from systeme_etudiant_app.forms import EditResultForm
from systeme_etudiant_app.models import Students, Subjects, StudentResult


class EditResultViewClass(View):
    def get(self, request):
        staff_id = request.user.id
        edit_result_form = EditResultForm(staff_id=staff_id)
        return render(request, "staff_template/edit_student_result.html", {"form": edit_result_form})

    def post(self, request, *args, **kwargs):
        form = EditResultForm(request.POST, staff_id=request.user.id)

        if form.is_valid():
            student_admin_id = form.cleaned_data['student_ids']   # <<< correction
            assignment_marks = form.cleaned_data['assignment_marks']
            exam_marks = form.cleaned_data['exam_marks']
            subject_id = form.cleaned_data['subject_id']

            # Récupérer les objets
            student_obj = Students.objects.get(admin=student_admin_id)
            subject_obj = Subjects.objects.get(id=subject_id)

            try:
                result = StudentResult.objects.get(
                    subject_id=subject_obj,
                    student_id=student_obj
                )
            except StudentResult.DoesNotExist:
                messages.error(request, "Aucun résultat trouvé pour cet étudiant.")
                return HttpResponseRedirect(reverse("edit_student_result"))

            # Mise à jour
            result.subject_assignment_marks = assignment_marks
            result.subject_exam_marks = exam_marks
            result.save()

            messages.success(request, "Successfully Updated Result")
            return HttpResponseRedirect(reverse("edit_student_result"))

        else:
            messages.error(request, "Failed To Update Result")
            return render(request, "staff_template/edit_student_result.html", {"form": form})
