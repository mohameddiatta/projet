from django.shortcuts import render
from django.views import View


class EditViewClass(View):
    def get(self,request,):
        return render(request,"edit_student_result.html")

    def post(self, request, *args, **kwargs):
        pass