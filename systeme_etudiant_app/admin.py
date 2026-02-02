from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Courses, Filiere, Niveau, Paiement, Inscription,
    Staffs, Students, FeedBackStudents, FeedBackStaffs,
    Notification, NotificationStaffs, NotificationStudents,
    Attendance, AttendanceReport, LeaveReportStudent, LeaveReportStaff, Subjects
)

# 1. CustomUser
admin.site.register(CustomUser, UserAdmin)

# 2. Enregistrements simples
admin.site.register([
    Courses, Filiere, Niveau, Staffs, Students,
    FeedBackStudents, FeedBackStaffs, Notification,
    NotificationStaffs, NotificationStudents, Attendance,
    AttendanceReport, LeaveReportStudent, LeaveReportStaff, Subjects
])


# 3. Inline pour les Paiements
class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 1
    readonly_fields = ('date_paiement',)
    fields = ('transaction_id', 'montant', 'methode', 'statut')


# 4. Configuration Inscription AMÉLIORÉE
@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    # Colonnes avec indicateurs des 4 documents
    list_display = (
        'id',
        'get_etudiant',
        'filiere',
        'niveau',
        'montant_total',
        'documents_status',
        'date_inscription',
        'statut_badge'
    )

    list_filter = ('filiere', 'niveau', 'date_inscription', 'statut')
    search_fields = ('students__admin__first_name', 'students__admin__last_name', 'students__admin__email')

    # Champs en lecture seule pour l'affichage
    readonly_fields = ('documents_summary', 'montant_info', 'date_inscription')

    # Organisation des champs avec sections claires
    fieldsets = (
        ("Informations Académiques", {
            'fields': ('students', 'filiere', 'niveau', 'statut')
        }),
        ("Informations Financières", {
            'fields': ('montant_total', 'montant_info')
        }),
        ("Documents Justificatifs", {
            'fields': ('documents_summary', 'diplome', 'piece_identite', 'photo', 'releve_notes'),
            'description': 'Les 4 documents requis pour l\'inscription'
        }),
        ("Dates", {
            'fields': ('date_inscription',)
        }),
    )

    inlines = [PaiementInline]

    # Méthodes pour l'affichage dans la liste
    def get_etudiant(self, obj):
        return f"{obj.students.admin.first_name} {obj.students.admin.last_name}"

    get_etudiant.short_description = "Étudiant"
    get_etudiant.admin_order_field = 'students__admin__last_name'

    def statut_badge(self, obj):
        if obj.statut == 'approuvé':
            return format_html('<span class="badge bg-success">✓ Approuvé</span>')
        elif obj.statut == 'rejeté':
            return format_html('<span class="badge bg-danger">✗ Rejeté</span>')
        else:
            return format_html('<span class="badge bg-warning">⏳ En attente</span>')

    statut_badge.short_description = "Statut"

    def documents_status(self, obj):
        """Affiche les 4 documents avec des icônes dans la liste"""
        icons = []

        # Diplôme
        if obj.diplome:
            icons.append('<span title="Diplôme présent" style="color:green;">📄</span>')
        else:
            icons.append('<span title="Diplôme manquant" style="color:red;">❓</span>')

        # Relevé de notes
        if obj.releve_notes:
            icons.append('<span title="Relevé présent" style="color:green;">📊</span>')
        else:
            icons.append('<span title="Relevé manquant" style="color:red;">❓</span>')

        # Pièce d'identité
        if obj.piece_identite:
            icons.append('<span title="CNI présente" style="color:green;">🆔</span>')
        else:
            icons.append('<span title="CNI manquante" style="color:red;">❓</span>')

        # Photo
        if obj.photo:
            icons.append('<span title="Photo présente" style="color:green;">📸</span>')
        else:
            icons.append('<span title="Photo manquante" style="color:red;">❓</span>')

        # Compter les documents présents
        total = 4
        present = sum([1 if obj.diplome else 0,
                       1 if obj.releve_notes else 0,
                       1 if obj.piece_identite else 0,
                       1 if obj.photo else 0])

        return format_html(
            '{} <small>({}/{})</small>',
            format_html(' '.join(icons)),
            present, total
        )

    documents_status.short_description = "Documents (4)"

    # Méthodes pour l'affichage détaillé (formulaire)
    def documents_summary(self, obj):
        """Aperçu des 4 documents dans le formulaire"""
        if not obj.id:
            return "Aucun document (inscription non sauvegardée)"

        html = '''
        <style>
            .doc-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                margin: 10px 0;
            }
            .doc-item {
                border: 1px solid #ddd;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
            }
            .doc-item.present {
                background-color: #d4edda;
                border-color: #c3e6cb;
            }
            .doc-item.missing {
                background-color: #f8d7da;
                border-color: #f5c6cb;
            }
            .doc-icon {
                font-size: 20px;
                margin-bottom: 5px;
            }
        </style>
        <div class="doc-grid">
        '''

        documents = [
            ('diplome', 'Diplôme', '📄'),
            ('releve_notes', 'Relevé de notes', '📊'),
            ('piece_identite', 'Pièce d\'identité', '🆔'),
            ('photo', 'Photo d\'identité', '📸')
        ]

        for field, label, icon in documents:
            file = getattr(obj, field)
            has_file = bool(file)

            html += f'''
            <div class="doc-item {'present' if has_file else 'missing'}">
                <div class="doc-icon">{icon}</div>
                <strong>{label}</strong><br>
            '''

            if has_file:
                html += f'''
                <a href="{file.url}" target="_blank" style="color: #155724;">
                    <small><i class="fas fa-eye"></i> Voir</small>
                </a>
                '''
            else:
                html += '''
                <small style="color: #721c24;">Manquant</small>
                '''

            html += '</div>'

        html += '</div>'

        # Compter les documents
        total = 4
        present = sum([1 if obj.diplome else 0,
                       1 if obj.releve_notes else 0,
                       1 if obj.piece_identite else 0,
                       1 if obj.photo else 0])

        html += f'''
        <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
            <strong>Résumé :</strong> {present}/{total} documents fournis
            <div class="progress" style="height: 8px; margin-top: 5px;">
                <div class="progress-bar bg-success" role="progressbar" 
                     style="width: {(present / total) * 100}%"></div>
            </div>
        </div>
        '''

        return format_html(html)

    documents_summary.short_description = "Aperçu des documents"

    def montant_info(self, obj):
        """Affiche les informations financières"""
        if not obj.id:
            return "Informations non disponibles"

        return format_html('''
            <div style="background: #e8f4fd; padding: 10px; border-radius: 5px;">
                <strong>Total à payer:</strong> {:,} FCFA<br>
                <strong>Déjà payé:</strong> {:,} FCFA<br>
                <strong>Reste à payer:</strong> {:,} FCFA<br>
                <div class="progress" style="height: 10px; margin-top: 5px;">
                    <div class="progress-bar bg-success" role="progressbar" 
                         style="width: {}%"></div>
                </div>
                <small>{}% payé</small>
            </div>
        ''',
           obj.montant_total,
           obj.montant_paye or 0,
           obj.reste_a_payer,
           obj.pourcentage_paye,
           round(obj.pourcentage_paye, 1)
           )

    montant_info.short_description = "Situation financière"

    # Actions personnalisées
    actions = ['approuver_inscriptions', 'rejeter_inscriptions']

    @admin.action(description="Approuver les inscriptions sélectionnées")
    def approuver_inscriptions(self, request, queryset):
        updated = queryset.update(statut='approuvé')
        self.message_user(request, f"{updated} inscription(s) approuvée(s).")

    @admin.action(description="Rejeter les inscriptions sélectionnées")
    def rejeter_inscriptions(self, request, queryset):
        updated = queryset.update(statut='rejeté')
        self.message_user(request, f"{updated} inscription(s) rejetée(s).")

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',)
        }


# 5. Configuration Paiement
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('inscription', 'transaction_id', 'montant', 'methode', 'statut_couleur', 'date_paiement')
    list_filter = ('statut', 'methode', 'date_paiement')
    search_fields = (
        'transaction_id',
        'inscription__students__admin__last_name',
        'inscription__students__admin__first_name'
    )
    actions = ['valider_paiements', 'rejeter_paiements']

    def statut_couleur(self, obj):
        colors = {'valide': '#28a745', 'en_attente': '#e67e22', 'echoue': '#dc3545'}
        return format_html(
            '<span style="color: white; background-color: {}; padding: 5px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            colors.get(obj.statut, '#6c757d'),
            obj.get_statut_display()
        )

    statut_couleur.short_description = 'Statut'

    @admin.action(description="Valider les paiements sélectionnés")
    def valider_paiements(self, request, queryset):
        queryset.update(statut='valide')
        self.message_user(request, f"{queryset.count()} paiement(s) validé(s).")

    @admin.action(description="Marquer comme échoués")
    def rejeter_paiements(self, request, queryset):
        queryset.update(statut='echoue')
        self.message_user(request, f"{queryset.count()} paiement(s) marqué(s) comme échoués.")