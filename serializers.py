from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Patient, Staff, Appointment, MedicalRecord, Prescription,
    Procedure, Department, Diagnosis, InsuranceCompany, CustomUser, AuditLog
)


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'user', 'role', 'phone', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class InsuranceCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceCompany
        fields = ['id', 'name', 'license_number', 'phone', 'email', 'address']


class DepartmentSerializer(serializers.ModelSerializer):
    head_doctor_name = serializers.CharField(source='head_doctor.full_name', read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'head_doctor', 'head_doctor_name', 'phone', 'cabinet_number']


class StaffSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Staff
        fields = [
            'id', 'user', 'full_name', 'date_of_birth', 'gender',
            'position', 'specialty', 'license_number', 'experience_years',
            'department', 'department_name', 'phone', 'email',
            'work_schedule', 'is_available'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = ['id', 'code', 'name', 'description', 'is_active']


class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    insurance_company_name = serializers.CharField(source='insurance_company.name', read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id', 'user', 'full_name', 'date_of_birth', 'age', 'gender',
            'passport_number', 'address', 'phone', 'email',
            'insurance_company', 'insurance_company_name', 'insurance_number',
            'emergency_contact', 'emergency_phone', 'allergies', 'chronic_diseases',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'age']

    def get_age(self, obj):
        return obj.age


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    doctor_specialty = serializers.CharField(source='doctor.specialty', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'doctor_specialty', 'appointment_date', 'appointment_time',
            'status', 'reason', 'notes', 'duration_minutes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id', 'medical_record', 'patient', 'patient_name', 'doctor',
            'doctor_name', 'medication_name', 'dosage', 'frequency',
            'duration_days', 'instructions', 'is_issued', 'valid_until',
            'created_at'
        ]
        read_only_fields = ['created_at']


class MedicalRecordSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    diagnosis_name = serializers.CharField(source='diagnosis.name', read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'patient', 'patient_name', 'appointment', 'doctor',
            'doctor_name', 'record_date', 'symptoms', 'diagnosis',
            'diagnosis_name', 'treatment_plan', 'notes', 'is_signed',
            'digital_signature', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'digital_signature']
