from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from enum import Enum
import uuid

# ============ ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ И ВЫБОРЫ ============

class GenderChoice(models.TextChoices):
    MALE = 'M', 'Мужской'
    FEMALE = 'F', 'Женский'
    OTHER = 'O', 'Другое'


class PositionChoice(models.TextChoices):
    DOCTOR = 'doctor', 'Врач'
    NURSE = 'nurse', 'Медсестра'
    REGISTRAR = 'registrar', 'Регистратор'


class AppointmentStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Запланирован'
    CONFIRMED = 'confirmed', 'Подтвержден'
    COMPLETED = 'completed', 'Завершен'
    CANCELLED = 'cancelled', 'Отменен'
    NO_SHOW = 'no_show', 'Не явился'


class RoleChoice(models.TextChoices):
    ADMIN = 'admin', 'Администратор'
    DOCTOR = 'doctor', 'Врач'
    NURSE = 'nurse', 'Медсестра'
    REGISTRAR = 'registrar', 'Регистратор'
    PATIENT = 'patient', 'Пациент'


# ============ СУЩНОСТЬ 1: ПОЛЬЗОВАТЕЛИ ============

class CustomUser(models.Model):
    """
    Расширенная модель пользователя с поддержкой ролей
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=RoleChoice.choices,
        default=RoleChoice.PATIENT
    )
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'custom_users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


# ============ СУЩНОСТЬ 2: СТРАХОВЫЕ КОМПАНИИ ============

class InsuranceCompany(models.Model):
    """
    Страховые компании
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'insurance_companies'
        verbose_name = 'Страховая компания'
        verbose_name_plural = 'Страховые компании'

    def __str__(self):
        return self.name


# ============ СУЩНОСТЬ 3: ПАЦИЕНТЫ ============

class Patient(models.Model):
    """
    Пациенты медицинского учреждения
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient')
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(
        validators=[
            MinValueValidator(limit_value='1900-01-01'),
        ]
    )
    gender = models.CharField(max_length=1, choices=GenderChoice.choices)
    passport_number = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    insurance_company = models.ForeignKey(
        InsuranceCompany,
        on_delete=models.SET_NULL,
        null=True,
        related_name='patients'
    )
    insurance_number = models.CharField(max_length=50, unique=True)
    emergency_contact = models.CharField(max_length=255)
    emergency_phone = models.CharField(max_length=20)
    allergies = models.TextField(blank=True)
    chronic_diseases = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patients'
        verbose_name = 'Пациент'
        verbose_name_plural = 'Пациенты'
        indexes = [
            models.Index(fields=['insurance_number']),
            models.Index(fields=['passport_number']),
        ]

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


# ============ СУЩНОСТЬ 4: ОТДЕЛЕНИЯ ============

class Department(models.Model):
    """
    Отделения медицинского учреждения
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    head_doctor = models.ForeignKey(
        'Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='department_head'
    )
    phone = models.CharField(max_length=20)
    cabinet_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departments'
        verbose_name = 'Отделение'
        verbose_name_plural = 'Отделения'

    def __str__(self):
        return self.name


# ============ СУЩНОСТЬ 5: МЕДИЦИНСКИЙ ПЕРСОНАЛ ============

class Staff(models.Model):
    """
    Сотрудники медицинского учреждения
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff')
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GenderChoice.choices)
    position = models.CharField(max_length=20, choices=PositionChoice.choices)
    specialty = models.CharField(max_length=255, blank=True)  # только для врачей
    license_number = models.CharField(max_length=50, unique=True)
    experience_years = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(70)]
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='staff_members'
    )
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    work_schedule = models.JSONField(default=dict)  # {"Monday": "09:00-17:00", ...}
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff'
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        indexes = [
            models.Index(fields=['position', 'department']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.get_position_display()})"


# ============ СУЩНОСТЬ 6: ПРИЕМЫ ============

class Appointment(models.Model):
    """
    Запись на прием к врачу
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='appointments',
        limit_choices_to={'position': PositionChoice.DOCTOR}
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED
    )
    reason = models.TextField()
    notes = models.TextField(blank=True)
    duration_minutes = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointments'
        verbose_name = 'Прием'
        verbose_name_plural = 'Приемы'
        unique_together = ('doctor', 'appointment_date', 'appointment_time')
        indexes = [
            models.Index(fields=['appointment_date', 'doctor']),
            models.Index(fields=['patient']),
        ]

    def __str__(self):
        return f"{self.patient.full_name} - {self.doctor.full_name} ({self.appointment_date})"


# ============ СУЩНОСТЬ 7: ДИАГНОЗЫ ============

class Diagnosis(models.Model):
    """
    Справочник диагнозов (МКБ-10)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    code = models.CharField(max_length=10, unique=True)  # Код МКБ-10
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diagnoses'
        verbose_name = 'Диагноз'
        verbose_name_plural = 'Диагнозы'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


# ============ СУЩНОСТЬ 8: МЕДИЦИНСКИЕ ЗАПИСИ ============

class MedicalRecord(models.Model):
    """
    Электронные истории болезни пациентов
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_record'
    )
    doctor = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name='medical_records',
        limit_choices_to={'position': PositionChoice.DOCTOR}
    )
    record_date = models.DateTimeField(default=timezone.now)
    symptoms = models.TextField()
    diagnosis = models.ForeignKey(
        Diagnosis,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medical_records'
    )
    treatment_plan = models.TextField()
    notes = models.TextField(blank=True)
    is_signed = models.BooleanField(default=False)
    digital_signature = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'medical_records'
        verbose_name = 'Медицинская запись'
        verbose_name_plural = 'Медицинские записи'
        indexes = [
            models.Index(fields=['patient', 'record_date']),
        ]

    def __str__(self):
        return f"Запись {self.patient.full_name} - {self.record_date.date()}"


# ============ СУЩНОСТЬ 9: НАЗНАЧЕНИЯ/РЕЦЕПТЫ ============

class Prescription(models.Model):
    """
    Назначения и рецепты врача
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name='prescriptions'
    )
    medication_name = models.CharField(max_length=500)
    dosage = models.CharField(max_length=100)  # например: "500mg x 2"
    frequency = models.CharField(max_length=100)  # например: "3 раза в день"
    duration_days = models.IntegerField()
    instructions = models.TextField()
    is_issued = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateField()

    class Meta:
        db_table = 'prescriptions'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f"{self.medication_name} для {self.patient.full_name}"


# ============ СУЩНОСТЬ 10: ПРОЦЕДУРЫ ============

class Procedure(models.Model):
    """
    Медицинские процедуры и анализы
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=500)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = 'procedures'
        verbose_name = 'Процедура'
        verbose_name_plural = 'Процедуры'

    def __str__(self):
        return self.name


# ============ СУЩНОСТЬ 11: ВЫПОЛНЕННЫЕ ПРОЦЕДУРЫ ============

class ProcedureRecord(models.Model):
    """
    История выполненных процедур пациентом
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='procedure_records')
    procedure = models.ForeignKey(Procedure, on_delete=models.PROTECT, related_name='records')
    performed_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)
    performed_date = models.DateTimeField()
    result = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procedure_records'
        verbose_name = 'Выполненная процедура'
        verbose_name_plural = 'Выполненные процедуры'

    def __str__(self):
        return f"{self.patient.full_name} - {self.procedure.name}"


# ============ СУЩНОСТЬ 12: ЛОГИ АУДИТА ============

class AuditLog(models.Model):
    """
    Логирование всех значимых действий в системе
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Лог аудита'
        verbose_name_plural = 'Логи аудита'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} ({self.timestamp})"
