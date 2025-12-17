from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Patient, Staff, Department, Appointment, MedicalRecord, Prescription, Diagnosis, InsuranceCompany, CustomUser
import csv


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'date_of_birth', 'gender', 'phone', 'export_buttons']
    search_fields = ['full_name', 'insurance_number', 'phone']
    list_filter = ['gender', 'insurance_company']
    
    def export_buttons(self, obj):
        """Кнопки экспорта"""
        return format_html(
            '<a class="button" href="{}">📄 TXT</a>&nbsp;'
            '<a class="button" href="{}">📊 CSV</a>&nbsp;'
            '<a class="button" href="{}">📋 JSON</a>',
            f'/admin/clinic/patient/{obj.id}/export_txt/',
            f'/admin/clinic/patient/{obj.id}/export_csv/',
            f'/admin/clinic/patient/{obj.id}/export_json/'
        )
    export_buttons.short_description = 'Экспорт'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<uuid:patient_id>/export_txt/', self.export_txt_view, name='patient-export-txt'),
            path('<uuid:patient_id>/export_csv/', self.export_csv_view, name='patient-export-csv'),
            path('<uuid:patient_id>/export_json/', self.export_json_view, name='patient-export-json'),
        ]
        return custom_urls + urls
    
    def export_txt_view(self, request, patient_id):
        """Экспорт в TXT"""
        patient = Patient.objects.get(id=patient_id)
        
        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="patient_{patient.full_name}.txt"'
        
        content = f"""
╔════════════════════════════════════════════════════════════╗
║       МЕДИЦИНСКАЯ КАРТА ПАЦИЕНТА                           ║
╚════════════════════════════════════════════════════════════╝

ФИО: {patient.full_name}
Дата рождения: {patient.date_of_birth}
Возраст: {patient.age} лет
Пол: {patient.get_gender_display()}
Номер полиса: {patient.insurance_number}
Адрес: {patient.address}
Телефон: {patient.phone}

╔════════════════════════════════════════════════════════════╗
║       МЕДИЦИНСКИЕ ЗАПИСИ                                   ║
╚════════════════════════════════════════════════════════════╝
"""
        
        records = MedicalRecord.objects.filter(patient=patient).order_by('-record_date')[:10]
        for i, record in enumerate(records, 1):
            content += f"""
Запись #{i}:
  📅 Дата: {record.record_date.date()}
  👨‍⚕️ Врач: {record.doctor.full_name}
  🩺 Симптомы: {record.symptoms}
  💊 Диагноз: {record.diagnosis.name if record.diagnosis else 'Не указан'}
  📝 Лечение: {record.treatment_plan}
{'─' * 60}
"""
        
        response.write(content)
        return response
    
    def export_csv_view(self, request, patient_id):
        """Экспорт в CSV с правильными колонками"""
        patient = Patient.objects.get(id=patient_id)
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="patient_{patient.full_name}.csv"'
        
        writer = csv.writer(response, delimiter=';')
        
        # Заголовки
        writer.writerow(['ФИО', 'Дата рождения', 'Возраст', 'Пол', 'Телефон', 'Номер полиса', 'Адрес'])
        
        # Данные пациента
        writer.writerow([
            patient.full_name,
            str(patient.date_of_birth),
            patient.age,
            patient.get_gender_display(),
            patient.phone,
            patient.insurance_number,
            patient.address
        ])
        
        # Пустая строка
        writer.writerow([])
        
        # Медицинские записи
        writer.writerow(['МЕДИЦИНСКИЕ ЗАПИСИ'])
        writer.writerow(['Дата', 'Врач', 'Симптомы', 'Диагноз', 'Лечение', 'Подписано'])
        
        records = MedicalRecord.objects.filter(patient=patient).order_by('-record_date')[:10]
        for record in records:
            writer.writerow([
                str(record.record_date.date()),
                record.doctor.full_name,
                record.symptoms,
                record.diagnosis.name if record.diagnosis else 'Не указан',
                record.treatment_plan,
                'Да' if record.is_signed else 'Нет'
            ])
        
        return response
    
    def export_json_view(self, request, patient_id):
        """Экспорт в JSON"""
        import json
        patient = Patient.objects.get(id=patient_id)
        
        records_data = []
        for record in MedicalRecord.objects.filter(patient=patient).order_by('-record_date')[:10]:
            records_data.append({
                'date': str(record.record_date.date()),
                'doctor': record.doctor.full_name,
                'symptoms': record.symptoms,
                'diagnosis': record.diagnosis.name if record.diagnosis else 'Не указан',
                'treatment': record.treatment_plan,
                'signed': record.is_signed
            })
        
        data = {
            'patient': {
                'full_name': patient.full_name,
                'date_of_birth': str(patient.date_of_birth),
                'age': patient.age,
                'gender': patient.get_gender_display(),
                'phone': patient.phone,
                'insurance_number': patient.insurance_number,
                'address': patient.address,
            },
            'medical_records': records_data,
            'total_records': len(records_data)
        }
        
        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="patient_{patient.full_name}.json"'
        return response


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'specialty', 'department', 'phone']
    list_filter = ['position', 'department']
    search_fields = ['full_name', 'specialty']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'status']
    list_filter = ['status', 'appointment_date']
    search_fields = ['patient__full_name', 'doctor__full_name']
    date_hierarchy = 'appointment_date'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'cabinet_number']
    search_fields = ['name']


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'record_date', 'diagnosis', 'is_signed']
    list_filter = ['is_signed', 'record_date']
    search_fields = ['patient__full_name']
    date_hierarchy = 'record_date'


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'medication_name', 'dosage', 'valid_until']
    list_filter = ['valid_until']
    search_fields = ['patient__full_name', 'medication_name']


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    search_fields = ['code', 'name']
    list_filter = ['is_active']


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_number', 'phone']
    search_fields = ['name', 'license_number']


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['user__username']
