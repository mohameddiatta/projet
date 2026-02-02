from django import forms
from django.contrib.sessions.models import Session
from django.forms import Select, ChoiceField
from django.utils import choices
from requests import session

from .models import CustomUser, SessionYearModel, Subjects
from django import forms
from .models import Students
from .models import Courses
from systeme_etudiant_app.models import Courses

class ChoiceNoValidation(ChoiceField):
    def validate(self, value):
        pass

class DateInput(forms.DateInput):
    input_type = "date"



class AddStudentForm(forms.Form):
    email = forms.EmailField(label="Email",max_length=50,widget=forms.EmailInput(attrs={"class":"form-control", "autocomplete":"off"}))
    password = forms.CharField(label="Password",max_length=50,widget=forms.PasswordInput(attrs={"class":"form-control"}))
    first_name = forms.CharField(label="First Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name = forms.CharField(label="Last Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    username = forms.CharField(label="Username",max_length=50,widget=forms.TextInput(attrs={"class":"form-control","autocomplete":"off"}))
    address = forms.CharField(label="Address",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))


    course_list=[]
    try:
       courses = Courses.objects.all()
       for course in courses:
           small_course=(course.id,course.course_name)
           course_list.append(small_course)
    except:
        course_list=[]

    session_list = []
    try:
        sessions = SessionYearModel.objects.all()
        for ses in sessions:
            small_ses = (ses.id, str(ses.session_start_year)+"  TO  "+str(ses.session_end_year))
            session_list.append(small_ses)
    except:
        session_list = []

    gender_choice={
        ("Male","Male"),
        ("Female","Female")
     }

    course = forms.ChoiceField(label="Course",choices=course_list,widget=forms.Select(attrs={"class":"form-control"}))
    sex = forms.ChoiceField(label="Sex",choices=gender_choice,widget=forms.Select(attrs={"class":"form-control"}))
    session_year_id = forms.ChoiceField(label="Session Year",widget=forms.Select(attrs={"class":"form-control"}),choices=session_list)
    profile_pic = forms.FileField(label="Profile Pic",max_length=200,widget=forms.FileInput(attrs={"class":"form-control"}))


class EditStudentForm(forms.Form):
    email = forms.EmailField(label="Email",max_length=100,widget=forms.EmailInput(attrs={"class":"form-control"}))
    first_name = forms.CharField(label="First Name",max_length=100,widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name = forms.CharField(label="Last Name",max_length=100,widget=forms.TextInput(attrs={"class":"form-control"}))
    username = forms.CharField(label="Username",max_length=100,widget=forms.TextInput(attrs={"class":"form-control"}))
    address = forms.CharField(label="Address",max_length=200,widget=forms.TextInput(attrs={"class":"form-control"}))

    course_liste=[]
    try:
        courses = Courses.objects.all()
        for course in courses:
            small_course=(course.id,course.course_name)
            course_liste.append(small_course)
    except:
        course_liste=[]


    session_list = []

    try:
        # Récupérer toutes les sessions
        sessions = SessionYearModel.objects.all()
        for ses in sessions:
            small_ses = (
                ses.id,
                f"{ses.session_start_year} TO {ses.session_end_year}"
            )
            session_list.append(small_ses)
    except Exception as e:
        print("Erreur récupération sessions:", e)
        session_list = []
    gender_choice={
        ("Male","Male"),
        ("Femele","Femele")
     }

    course = forms.ChoiceField(label="Course",choices=course_liste,widget=forms.Select(attrs={"class":"form-control"}))
    sex = forms.ChoiceField(label="Sex",choices=gender_choice,widget=forms.Select(attrs={"class":"form-control"}))
    session_year_id = forms.ChoiceField(label="Session Year",widget=forms.Select(attrs={"class":"form-control"}),choices=session_list)
    profile_pic = forms.FileField(label="Profile Pic",max_length=50,widget=forms.FileInput(attrs={"class":"form-control"}),required=False)




class StaffForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=150)
    address = forms.CharField(widget=forms.Textarea)

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exists():
            user = CustomUser.objects.get(username=username)
            if hasattr(user, 'staffs'):
                raise forms.ValidationError("Un staff avec ce nom d'utilisateur existe déjà")
        return username

    class Meta:
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'address']


class EditResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.self_id=kwargs.pop("staff_id")
        super(EditResultForm,self).__init__(*args,**kwargs)
        subject_list=[]
        try:
            subjects=Subjects.objects.filter(staff_id=self.self_id)
            for subject in subjects:
                subject_single=(subject.id,subject.subject_name)
                subject_list.append(subject_single)
        except:
            subject_list=[]

        self.fields['subject_id'].choices=subject_list

    session_list=[]
    try:
        sessions=SessionYearModel.objects.all()
        for session in sessions:
            session_singl=(session.id,str(session.session_start_year)+" To "+str(session.session_end_year))
            session_list.append(session_singl)
    except:
        session_list=[]
    subject_id=forms.ChoiceField(label="Subject",widget=forms.Select(attrs={"class":"form-control"}))
    session_id=forms.ChoiceField(label="Session Year",choices=session_list,widget=forms.Select(attrs={"class":"form-control"}))
    student_ids=ChoiceNoValidation(label="Student",widget=forms.Select(attrs={"class":"form-control"}))
    assignment_marks=forms.CharField(label="Assignment Marks",widget=forms.TextInput(attrs={"class":"form-control"}))
    exam_marks=forms.CharField(label="Exam Marks",widget=forms.TextInput(attrs={"class":"form-control"}))


# forms.py - Formulaire adapté à votre structure
from django import forms
from .models import Students, CustomUser


class CompleteStudentProfileForm(forms.Form):
    # Champs depuis CustomUser
    first_name = forms.CharField(
        label="Prénom",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom'
        })
    )

    last_name = forms.CharField(
        label="Nom",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom'
        })
    )

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com'
        })
    )

    # Champs additionnels
    telephone = forms.CharField(
        label="Téléphone",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+33 6 12 34 56 78'
        })
    )

    numero_ine = forms.CharField(
        label="Numéro INE",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234567890A'
        })
    )

    date_naissance = forms.DateField(
        label="Date de naissance",
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    adresse = forms.CharField(
        label="Adresse complète",
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Numéro, rue, code postal, ville'
        })
    )

    GENDER_CHOICES = [
        ('Male', 'Masculin'),
        ('Female', 'Féminin'),
    ]

    gender = forms.ChoiceField(
        label="Genre",
        choices=GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    profile_pic = forms.ImageField(
        label="Photo de profil",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file'
        })
    )