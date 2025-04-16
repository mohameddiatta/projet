from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _

from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, "HOD"),        # Head of Department/Admin
        (2, "Staff"),      # Personnel
        (3, "Student"),    # Étudiant
    )
    
    user_type = models.PositiveSmallIntegerField(
        choices=USER_TYPE_CHOICES,
        default=1,
        verbose_name=_("Type d'utilisateur")
    )

    # Correction des relations ManyToMany
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groupes'),
        blank=True,
        help_text=_('Les groupes auxquels appartient cet utilisateur. Un utilisateur obtient toutes les permissions accordées à chacun de ses groupes.'),
        related_name="customuser_set",
        related_query_name="customuser",
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions utilisateur'),
        blank=True,
        help_text=_('Permissions spécifiques pour cet utilisateur.'),
        related_name="customuser_permissions_set",
        related_query_name="customuser_permission",
    )
class Meta:
    db_table = 's_ope.customuser'
        

    def __str__(self):
        return self.username

class AdminHOD(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        db_table = 's_ope.adminHod'

    def __str__(self):
        return self.admin

class Staffs(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        db_table = 's_ope.staffs'

    def __str__(self):
        return self.admin.username

class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    class Meta:
        db_table = 's_ope.courses'

    def __str__(self):
        return self.course_name

class Subjects(models.Model):
    id = models.AutoField(primary_key=True)
    subject_name = models.CharField(max_length=255)
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE,default=1)
    staff_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        db_table = 's_ope.subjects'

    def __str__(self):
        return self.subject_name

class Students(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True)
    gender = models.CharField(max_length=255)
    profile_pic = models.ImageField()
    address = models.TextField()
    course_id = models.ForeignKey('Courses', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        db_table = 's_ope.students'

    def __str__(self):
        return self.admin.username
    
class Filiere(models.Model):
    ID_filiere = models.AutoField(primary_key=True)
    Nom_filiere = models.CharField(max_length=255)
    Quota_Max = models.IntegerField()

    class Meta:
        db_table = 's_ope.filiere'

    def __str__(self):
        return self.Nom_Filiere

class Inscription(models.Model):
    students = models.ForeignKey(Students, on_delete=models.CASCADE)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE)  # Vérifie que Filiere est définie au-dessus
    date_inscription = models.DateField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        db_table = 's_ope.inscription'
        unique_together = ('students', 'filiere')

    def __str__(self):
        return f"{self.students} inscrit à {self.filiere}"



class Attendance(models.Model):
    id=models.AutoField(primary_key=True)
    subject_id=models.ForeignKey(Subjects,on_delete=models.DO_NOTHING)
    session_start_year=models.DateField()
    session_end_year=models.DateField()
    attendance_date=models.DateTimeField(auto_now_add=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 's_ope.attendance'

    def __str__(self):
        return f"Présence - {self.subject_id} - {self.attendance_date}"


class AttendanceReport(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.DO_NOTHING)
    attendance_id=models.ForeignKey(Attendance,on_delete=models.CASCADE)
    status=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 's_ope.attendance_report'

    def __str__(self):
        return f"{self.student_id} - {self.attendance_id} - {'Présent' if self.status else 'Absent'}"

class LeaveReportStudent(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.CASCADE)
    leave_date=models.CharField(max_length=255)
    leave_message=models.TextField()
    leave_status=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 's_ope.leave_report_student'

    def __str__(self):
        return f"Demande - {self.student_id} - {self.leave_date}"

class LeaveReportStaff(models.Model):
    id=models.AutoField(primary_key=True)
    staff_id=models.ForeignKey(Staffs,on_delete=models.CASCADE)
    leave_date=models.CharField(max_length=255)
    leave_message=models.TextField()
    leave_status=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 's_ope.leave_report_staff'

    def __str__(self):
        return f"Demande - {self.staff_id} - {self.leave_date}"

from django.db import models

class Notification(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message



class FeedBackStudent(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.CASCADE)
    feedBack_reply=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 's_ope.feedback_student'

    def __str__(self):
        return f"Feedback - {self.student_id}"

class FeedBackStaff(models.Model):
    id=models.AutoField(primary_key=True)
    staff_id=models.ForeignKey(Staffs,on_delete=models.CASCADE)
    feedBack_reply=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 's_ope.notification_staff'

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.staff = None

    def __str__(self):
        return f"Notif Staff {self.staff}"



class NotificationStudent(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.CASCADE)
    message=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 's_ope.notification'

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None

    def __str__(self):
        return f"Notif {self.id} - {self.user}"

class NotificationStaff(models.Model):
    id=models.AutoField(primary_key=True)
    staff_id=models.ForeignKey(Staffs,on_delete=models.CASCADE)
    feedBack_date=models.CharField(max_length=255)
    feedBack_reply=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 's_ope.notification_staff_unique'

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.staff = None

    def __str__(self):
        return f"Notif Staff {self.staff}"



# 🔹 Niveau
class Niveau(models.Model):
    id = models.AutoField(primary_key=True)
    nom_niveau = models.CharField(max_length=255)
    objects = models.Manager()

    class Meta:
        db_table = 's_ope.niveau'

    def __str__(self):
        return self.nom_niveau

# 🔹 Paiement
class Paiement(models.Model):
    METHODES_PAIEMENT = [
        ('orange_money', 'Orange Money'),
        ('wave', 'Wave'),
        ('free_money', 'Free Money'),
    ]

    STATUTS_PAIEMENT = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('echoue', 'Échoué'),
    ]

    id = models.AutoField(primary_key=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField(auto_now_add=True)
    methode = models.CharField(max_length=20, choices=METHODES_PAIEMENT)
    statut = models.CharField(max_length=20, choices=STATUTS_PAIEMENT, default='en_attente')
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE)
    objects = models.Manager()

    class Meta:
        db_table = 's_ope.paiement'

    def __str__(self):
        return f"{self.inscription} - {self.methode} ({self.statut})"





class Document(models.Model):
    ID_Document = models.AutoField(primary_key=True)
    Nom_Document = models.CharField(max_length=255)
    Chemin_Fichier = models.FileField(upload_to='documents/')
    ID_Inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE)
    objects = models.Manager()

    class Meta:
        db_table = 's_ope.document'

    def __str__(self):
        return self.Nom_Document




@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            AdminHOD.objects.create(admin=instance)
        if instance.user_type == 2:
            Staffs.objects.create(admin=instance)
        if instance.user_type == 3:
            Students.objects.create(admin=instance,Course_id=Courses.objects.get(id=1),session_start_yea="2020-01-01",session_end_yea="2021-01-01",address="",profile_pic="",gender="")

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
   if instance.user_type == 1:
    instance.adminhod.save()
   if instance.user_type == 2:
      instance.staffs.save()
   if instance.user_type == 3:
     instance.students.save()

        
        
