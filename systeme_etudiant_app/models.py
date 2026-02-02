from email.policy import default


from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.core.mail import send_mail
from django.db.models import Sum




# creation des models
class SessionYearModel(models.Model):
    id=models.AutoField(primary_key=True)
    session_start_year=models.DateField()
    session_end_year=models.DateField()
    sync_fix = models.BooleanField(default=True)
    objects=models.Manager()

    class Meta:
        db_table = 'session_year_model'  # nom clair dans PostgreSQL

    def __str__(self):
        return f"{self.session_start_year} - {self.session_end_year}"

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
    email = models.EmailField(unique=True)

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
      db_table = 'customuser'


    def __str__(self):
        return self.username

class AdminHOD(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        db_table = 'adminHod'

    def __str__(self):
        return self.admin

class Staffs(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    fcm_token=models.TextField(default="")
    objects = models.Manager()

    class Meta:
        db_table = 'staffs'

    def __str__(self):
        return self.admin.username

class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    class Meta:
        db_table = 'courses'

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
        db_table = 'subjects'

    def __str__(self):
        return self.subject_name


class Students(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True)
    gender = models.CharField(max_length=255)
    profile_pic = models.ImageField(upload_to='students/', null=True, blank=True)
    address = models.TextField()
    course_id = models.ForeignKey('Courses', on_delete=models.DO_NOTHING, null=True, blank=True)
    session_year_id = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE)

    # ========== AJOUTEZ CES CHAMPS ==========
    STATUS_CHOICES = [
        ('pending', '⏳ En attente'),
        ('approved', '✅ Approuvé'),
        ('rejected', '❌ Rejeté'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut de validation"
    )
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name="Raison du rejet"
    )
    validated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )
    validated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_students',
        verbose_name="Validé par"
    )
    # ========================================

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fcm_token = models.TextField(default="")
    objects = models.Manager()

    class Meta:
        db_table = 'students'

    def __str__(self):
        return self.admin.username

    # Méthode pour vérifier si approuvé
    def is_approved(self):
        return self.status == 'approved'

class Filiere(models.Model):
    FILIERES = [
        ('ADMIN', 'Administration'),
        ('IG', 'Informatique de Gestion'),
        ('ELECTRO', 'Électromécanique'),
    ]

    ID_filiere = models.AutoField(primary_key=True)
    Nom_filiere = models.CharField(max_length=20, choices=FILIERES, unique=True)
    Quota_Max = models.IntegerField()
    objects = models.Manager()

    class Meta:
        db_table = 'filiere'

    def __str__(self):
        return self.get_Nom_filiere_display()



class Niveau(models.Model):
    NIVEAUX = [
        ('AP', 'AP'),
        ('Licence 1', 'Licence 1'),
        ('Licence 2', 'Licence 2'),
        ('Licence 3', 'Licence 3'),
        ('Master 1', 'Master 1'),
        ('Master 2', 'Master 2'),
    ]

    id = models.AutoField(primary_key=True)
    nom_niveau = models.CharField(max_length=20, choices=NIVEAUX, unique=True)
    frais_base = models.IntegerField(default=60000, help_text="Frais d'inscription de base pour ce niveau")
    objects = models.Manager()

    class Meta:
        db_table = 'niveau'

    def __str__(self):
        return self.nom_niveau


class Inscription(models.Model):
    students = models.ForeignKey(Students, on_delete=models.CASCADE)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE)
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, default=1)
    statut = models.CharField(max_length=20, default='en_attente')
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Documents
    diplome = models.FileField(upload_to='diplomes/%Y/%m/', blank=True, null=True)
    piece_identite = models.FileField(upload_to='identite/%Y/%m/', blank=True, null=True)
    photo = models.FileField(upload_to='photos/%Y/%m/', blank=True, null=True)
    releve_notes = models.FileField(upload_to='releves/', null=True, blank=True)

    date_inscription = models.DateField(auto_now_add=True)
    last_sync_check = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    def save(self, *args, **kwargs):
        if not self.pk:  # Nouveau dossier seulement
            self.calculer_montant()
        super().save(*args, **kwargs)

    def calculer_montant(self):
        code_filiere = str(self.filiere.Nom_filiere).strip().upper()
        nom_niveau = str(self.niveau.nom_niveau).strip().upper()

        montant = self.niveau.frais_base

        filiere_speciales = ["EM", "IG", "AD", "ADMIN"]
        if code_filiere in filiere_speciales and nom_niveau not in ["AP", "LICENCE 1"]:
            montant += 5000

        if nom_niveau == "LICENCE 1":
            montant += 15000
        elif nom_niveau in ["LICENCE 2", "LICENCE 3"]:
            montant += 20000
        elif "MASTER" in nom_niveau:
            montant += 25000

        self.montant_total = montant

    # --- Propriétés Financières ---
    @property
    def montant_paye(self):
        # On calcule la somme des paiements validés en temps réel
        total = self.paiement_set.filter(statut__in=['valide', 'validé']).aggregate(total=Sum('montant'))['total']
        return total or 0

    @property
    def reste_a_payer(self):
        # Si le payé dépasse le total, on affiche 0 au lieu d'un chiffre négatif
        reste = self.montant_total - self.montant_paye
        return max(0, reste)

    @property
    def pourcentage_paye(self):
        if self.montant_total > 0:
            p = (float(self.montant_paye) / float(self.montant_total)) * 100
            return min(100.0, p)  # On bloque la barre de progression à 100% maximum
        return 0

    def __str__(self):
        return f"{self.students} - {self.filiere}"

    @property
    def liste_documents(self):
        """
        Retourne la liste des 4 documents avec leur statut
        Utilisé dans le template mes_inscriptions.html
        """
        return [
            {
                'nom': 'Diplôme',
                'type': 'diplome',
                'present': bool(self.diplome),
                'url': self.diplome.url if self.diplome else None,
                'icone': 'fas fa-file-pdf',
                'obligatoire': True
            },
            {
                'nom': 'Relevé de notes',
                'type': 'releve_notes',
                'present': bool(self.releve_notes),
                'url': self.releve_notes.url if self.releve_notes else None,
                'icone': 'fas fa-file-alt',
                'obligatoire': True
            },
            {
                'nom': 'Pièce d\'identité',
                'type': 'piece_identite',
                'present': bool(self.piece_identite),
                'url': self.piece_identite.url if self.piece_identite else None,
                'icone': 'fas fa-id-card',
                'obligatoire': True
            },
            {
                'nom': 'Photo d\'identité',
                'type': 'photo',
                'present': bool(self.photo),
                'url': self.photo.url if self.photo else None,
                'icone': 'fas fa-camera',
                'obligatoire': True
            }
        ]

    @property
    def documents_presents(self):
        """Retourne seulement les documents présents"""
        return [doc for doc in self.liste_documents if doc['present']]

    @property
    def documents_manquants(self):
        """Retourne les noms des documents manquants"""
        return [doc['nom'] for doc in self.liste_documents if not doc['present']]

    @property
    def nombre_documents(self):
        """Nombre total de documents (toujours 4)"""
        return 4

    @property
    def nombre_documents_presents(self):
        """Nombre de documents fournis"""
        return len(self.documents_presents)

    @property
    def pourcentage_documents(self):
        """Pourcentage de documents fournis"""
        if self.nombre_documents > 0:
            return (self.nombre_documents_presents / self.nombre_documents) * 100
        return 0

    @property
    def dossier_complet(self):
        """Vérifie si tous les documents sont fournis"""
        return self.nombre_documents_presents == self.nombre_documents

    class Meta:
        db_table = 'inscription'
        unique_together = ('students', 'filiere', 'niveau')


class Attendance(models.Model):
    id=models.AutoField(primary_key=True)
    subject_id=models.ForeignKey(Subjects,on_delete=models.DO_NOTHING)
    attendance_date=models.DateField()
    created_at=models.DateTimeField(auto_now_add=True)
    session_year_id=models.ForeignKey(SessionYearModel,on_delete=models.CASCADE)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 'attendance'

    def __str__(self):
        return f"Présence - {self.subject_id} - {self.attendance_date}"


class AttendanceReport(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.DO_NOTHING)
    attendance_id=models.ForeignKey(Attendance,on_delete=models.CASCADE)
    status=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 'attendance_report'

    def __str__(self):
        return f"{self.student_id} - {self.attendance_id} - {'Présent' if self.status else 'Absent'}"

class LeaveReportStudent(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.CASCADE)
    leave_date=models.CharField(max_length=255)
    leave_message=models.TextField()
    leave_status=models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 'leave_report_student'

    def __str__(self):
        return f"Demande - {self.student_id} - {self.leave_date}"

class LeaveReportStaff(models.Model):
    id=models.AutoField(primary_key=True)
    staff_id=models.ForeignKey(Staffs,on_delete=models.CASCADE)
    leave_date=models.CharField(max_length=255)
    leave_message=models.TextField()
    leave_status=models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 'leave_report_staff'

    def __str__(self):
        return f"Demande - {self.staff_id} - {self.leave_date}"

from django.db import models

class Notification(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message



class FeedBackStudents(models.Model):
    id=models.AutoField(primary_key=True)
    student_id=models.ForeignKey(Students,on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    objects=models.Manager()

    class Meta:
        db_table = 'feedback_students'

    def __str__(self):
        return f"Feedback - {self.student_id}"

class FeedBackStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    class Meta:
        db_table = 'feedback_staffs'

    def __str__(self):
        return f"Feedback de {self.staff_id.admin.username}"



class NotificationStudents(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        db_table = 'notification'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def __str__(self):
        return f"Notif {self.id} - {self.user}"

class NotificationStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        db_table = 'notification_staff_unique'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.staff = None

    def __str__(self):
        return f"Notif Staff {self.staff}"






# 🔹 Paiement
transaction_validator = RegexValidator(
    regex=r'^[A-Z0-9]{6,25}$',
    message="Le numéro de transaction doit contenir entre 6 et 25 caractères (lettres majuscules et chiffres)."

)

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

    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField(auto_now_add=True)
    methode = models.CharField(max_length=20, choices=METHODES_PAIEMENT)

    transaction_id = models.CharField(max_length=25,unique=True,validators=[transaction_validator],  # 🔹 ICI : Applique ta Regex
        help_text="Entrez le code reçu par SMS (ex: OM123...)"
    )
    recu = models.FileField(upload_to='preuves_paiement/', null=True, blank=True,
                            help_text="Capture d'écran ou reçu PDF")

    statut = models.CharField(max_length=20, choices=STATUTS_PAIEMENT, default='en_attente')
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE)
    objects= models.Manager()

    class Meta:
        db_table = 'paiement'

    def clean(self):
        if self.methode == 'orange_money' and not self.transaction_id.startswith('OM'):
            raise ValidationError("Transaction Orange Money invalide (doit commencer par OM).")

        if self.methode == 'wave' and not self.transaction_id.startswith('WV'):
            raise ValidationError("Transaction Wave invalide (doit commencer par WV).")

        if self.methode == 'free_money' and not self.transaction_id.startswith('FM'):
            raise ValidationError("Transaction Free Money invalide (doit commencer par FM).")

    def save(self, *args, **kwargs):
        if self.transaction_id:
            self.transaction_id = self.transaction_id.strip().upper()
        self.full_clean()  # 🔥 force toutes les validations
        super().save(*args, **kwargs)



class StudentResult(models.Model):
    id=models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students,on_delete=models.CASCADE)
    subject_id = models.ForeignKey(Subjects,on_delete=models.CASCADE)
    subject_exam_marks = models.FloatField(default=0)
    subject_assignment_marks = models.FloatField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now_add=True)


    objects = models.Manager()

    class Meta:
        db_table = 'student_result'
    def __str__(self):
       return f"{self.student_id}-{self.subject_id}"



@receiver(post_save, sender=Paiement)
def notifier_etudiant_paiement(sender, instance, created, **kwargs):
    # On vérifie si ce n'est pas une création (donc une modification)
    # et si le statut vient de passer à 'valide'
    if not created and instance.statut == 'valide':
        try:
            subject = 'Paiement Validé - Confirmation d\'Inscription'
            message = f"Bonjour {instance.inscription.students.admin.first_name},\n\n" \
                      f"Nous vous informons que votre paiement de {instance.montant} FCFA " \
                      f"(Référence: {instance.transaction_id}) a été validé avec succès.\n" \
                      f"Vous pouvez dès à présent télécharger votre reçu sur votre espace étudiant.\n\n" \
                      f"Cordialement,\nLe Service de la Scolarité."

            recipient_list = [instance.inscription.students.admin.email]
            send_mail(subject, message, 'votre_email@univ.edu', recipient_list)
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email : {e}")




@receiver(post_save,sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            AdminHOD.objects.create(admin=instance)
        elif instance.user_type == 2:
            Staffs.objects.get_or_create(admin=instance,address="")
        elif instance.user_type == 3:
            Students.objects.get_or_create(
                admin=instance,
                defaults={
                    'course_id': Courses.objects.first(),
                    'session_year_id': SessionYearModel.objects.first(),
                    'address': "",
                    'profile_pic': "",
                    'gender': ""
                }
            )


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    try:
        if instance.user_type == 1 and hasattr(instance, 'adminhod'):
            instance.adminhod.save()
        elif instance.user_type == 2 and hasattr(instance, 'staffs'):
            instance.staffs.save()
        elif instance.user_type == 3 and hasattr(instance, 'students'):
            instance.students.save()
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du profil utilisateur: {e}")


        
