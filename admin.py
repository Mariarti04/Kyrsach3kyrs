from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CustomUser, Patient, Staff, Department, Appointment,
    MedicalRecord, Prescription, Procedure, ProcedureRecord,
    InsuranceCompany, Diagnosis, AuditLog
)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_number', 'phone', 'email')
    search_fields = ('name', 'license_number')
    list_per_page = 20


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'head_doctor', 'phone', 'cabinet_number')
    search_fields = ('name', 'description')
    list_per_page = 20


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'insurance_number', 'phone', 'gender', 'age_display', 'created_at'
    )
    list_filter = ('gender', 'created_at', 'insurance_company')
    search_fields = ('full_name', 'insurance_number', 'passport_number')
    readonly_fields = ('id', 'created_at', 'updated_at', 'age_display')
    fieldsets = (
        ('Личная информация', {
            'fields': ('user', 'full_name', 'date_of_birth', 'gender', 'age_display')
        }),
        ('Документы', {
            'fields': ('passport_number', 'insurance_number', 'insurance_company')
        }),
        ('Контактная информация', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Чрезвычайные контакты', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('Медицинская информация', {
            'fields': ('allergies', 'chronic_diseases')
        }),
        ('Дата и время', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def age_display(self, obj):
        return obj.age
    age_display.short_description = 'Возраст'


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'position', 'specialty', 'department', 'license_number', 'is_available'
    )
    list_filter = ('position', 'department', 'is_available')
    search_fields = ('full_name', 'license_number', 'specialty')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Личная информация', {
            'fields': ('user', 'full_name', 'date_of_birth', 'gender')
        }),
        ('Должность и специальность', {
            'fields': ('position', 'specialty', 'license_number', 'experience_years')
        }),
        ('Место работы', {
            'fields': ('department', 'phone', 'email')
        }),
        ('График', {
            'fields': ('work_schedule', 'is_available')
        }),
        ('Дата и время', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'patient', 'doctor', 'appointment_date', 'appointment_time', 'status_badge'
    )
    list_filter = ('status', 'appointment_date', 'doctor')
    search_fields = ('patient__full_name', 'doctor__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'appointment_date'
    fieldsets = (
        ('Основная информация', {
            'fields': ('patient', 'doctor', 'status')
        }),
        ('Дата и время', {
            'fields': ('appointment_date', 'appointment_time', 'duration_minutes')
        }),
        ('Причина и примечания', {
            'fields': ('reason', 'notes')
        }),
        ('Время создания', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'scheduled': '#FFA500',
            'confirmed': '#0000CD',
            'completed': '#008000',
            'cancelled': '#FF0000',
            'no_show': '#808080',
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    list_per_page = 50


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = (
        'patient', 'doctor', 'record_date', 'diagnosis', 'is_signed_badge'
    )
    list_filter = ('record_date', 'is_signed', 'doctor')
    search_fields = ('patient__full_name', 'doctor__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'digital_signature')
    date_hierarchy = 'record_date'
    fieldsets = (
        ('Пациент и врач', {
            'fields': ('patient', 'doctor', 'appointment')
        }),
        ('Клиническая информация', {
            'fields': ('record_date', 'symptoms', 'diagnosis', 'treatment_plan', 'notes')
        }),
        ('Подпись', {
            'fields': ('is_signed', 'digital_signature'),
            'classes': ('collapse',)
        }),
        ('Дата и время', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_signed_badge(self, obj):
        if obj.is_signed:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Подписана</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Не подписана</span>'
        )
    is_signed_badge.short_description = 'Статус подписи'


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        'medication_name', 'patient', 'doctor', 'dosage', 'frequency', 'valid_until'
    )
    list_filter = ('is_issued', 'valid_until', 'created_at')
    search_fields = ('medication_name', 'patient__full_name')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('Пациент и врач', {
            'fields': ('medical_record', 'patient', 'doctor')
        }),
        ('Лекарственное средство', {
            'fields': ('medication_name', 'dosage', 'frequency', 'duration_days')
        }),
        ('Инструкции', {
            'fields': ('instructions', 'is_issued', 'valid_until')
        }),
        ('Дата создания', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'cost', 'duration_minutes', 'is_available')
    list_filter = ('department', 'is_available')
    search_fields = ('name', 'description')
    list_per_page = 25


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'timestamp')
    list_filter = ('action', 'timestamp', 'model_name')
    search_fields = ('user__username', 'action', 'model_name')
    readonly_fields = ('id', 'user', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'timestamp')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
