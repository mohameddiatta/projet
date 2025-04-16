from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from systeme_etudiant_app.models import CustomUser
from .models import Courses  # si c’est Courses au lieu de Course
from .models import Staffs
from .models import Students
from .models import Subjects

from .models import (
    Courses,
    Filiere,
    Niveau,
    Paiement,
    Inscription,
    Staffs,
    Students,
    Document,
    FeedBackStudent,
    Notification,
    NotificationStaff,
    Attendance,
    AttendanceReport,
    LeaveReportStudent,
    LeaveReportStaff,
    Subjects,
)

# Enregistrement simple des modèles
admin.site.register(Courses)
admin.site.register(Filiere)
admin.site.register(Niveau)
admin.site.register(Paiement)
admin.site.register(Inscription)
admin.site.register(Staffs)
admin.site.register(Students)
admin.site.register(Document)
admin.site.register(FeedBackStudent)
admin.site.register(Notification)
admin.site.register(NotificationStaff)
admin.site.register(Attendance)
admin.site.register(AttendanceReport)
admin.site.register(LeaveReportStudent)
admin.site.register(LeaveReportStaff)
admin.site.register(Subjects)

# Enregistrement du CustomUser avec UserAdmin
admin.site.register(CustomUser, UserAdmin)
