from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from datetime import datetime, timedelta, time
import csv
from io import StringIO

from .models import (
    Patient, Staff, Appointment, MedicalRecord, Prescription,
    Department, Diagnosis
)
from .serializers import (
    PatientSerializer, StaffSerializer, AppointmentSerializer,
    MedicalRecordSerializer, PrescriptionSerializer, DepartmentSerializer
)

import logging
logger = logging.getLogger(__name__)


def log_audit(user, action, model, object_id):
    """Простая функция логирования"""
    try:
        logger.info(f"User {user} performed {action} on {model} {object_id}")
    except:
        pass


# ============ ПАЦИЕНТЫ ============

class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    queryset = Patient.objects.all()

    def perform_create(self, serializer):
        patient = serializer.save()
        log_audit(self.request.user, 'create', 'Patient', str(patient.id))

    @action(detail=True, methods=['get'])
    def medical_records(self, request, pk=None):
        """Получить все медицинские записи пациента"""
        patient = self.get_object()
        records = MedicalRecord.objects.filter(patient=patient)
        serializer = MedicalRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def prescriptions(self, request, pk=None):
        """Получить все рецепты пациента"""
        patient = self.get_object()
        prescriptions = Prescription.objects.filter(patient=patient)
        return Response(PrescriptionSerializer(prescriptions, many=True).data)

    @action(detail=True, methods=['get'])
    def export_json(self, request, pk=None):
        """Экспорт данных пациента в JSON"""
        patient = self.get_object()
        data = {
            'patient': PatientSerializer(patient).data,
            'medical_records': MedicalRecordSerializer(
                MedicalRecord.objects.filter(patient=patient),
                many=True
            ).data,
            'appointments': AppointmentSerializer(
                Appointment.objects.filter(patient=patient),
                many=True
            ).data,
            'exported_at': datetime.now().isoformat()
        }
        log_audit(request.user, 'export_json', 'Patient', str(patient.id))
        return Response(data)

    @action(detail=True, methods=['get'])
    def export_csv(self, request, pk=None):
        """Экспорт данных пациента в CSV"""
        patient = self.get_object()

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="patient_{patient.full_name}.csv"'

        writer = csv.writer(response)
        writer.writerow(['ФИО', 'Дата рождения', 'Пол', 'Номер полиса', 'Адрес', 'Телефон'])
        writer.writerow([
            patient.full_name,
            patient.date_of_birth,
            patient.get_gender_display(),
            patient.insurance_number,
            patient.address,
            patient.phone
        ])

        log_audit(request.user, 'export_csv', 'Patient', str(patient.id))
        return response

    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        """Экспорт медицинской карты пациента"""
        patient = self.get_object()
        
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
║       ПОСЛЕДНИЕ МЕДИЦИНСКИЕ ЗАПИСИ                         ║
╚════════════════════════════════════════════════════════════╝
"""
        
        records = MedicalRecord.objects.filter(patient=patient)[:5]
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
        log_audit(request.user, 'export_pdf', 'Patient', str(patient.id))
        return response


# ============ ПЕРСОНАЛ ============

class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]
    queryset = Staff.objects.all()

    def perform_create(self, serializer):
        staff = serializer.save()
        log_audit(self.request.user, 'create', 'Staff', str(staff.id))

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Расписание врача на неделю"""
        doctor = self.get_object()
        appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__gte=timezone.now().date(),
            appointment_date__lte=timezone.now().date() + timedelta(days=7)
        ).order_by('appointment_date', 'appointment_time')
        return Response(AppointmentSerializer(appointments, many=True).data)

    @action(detail=True, methods=['get'])
    def patients(self, request, pk=None):
        """Список пациентов врача"""
        doctor = self.get_object()
        appointments = Appointment.objects.filter(doctor=doctor).values_list('patient', flat=True).distinct()
        patients = Patient.objects.filter(id__in=appointments)
        return Response(PatientSerializer(patients, many=True).data)


# ============ ОТДЕЛЕНИЯ ============

class DepartmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def perform_create(self, serializer):
        department = serializer.save()
        log_audit(self.request.user, 'create', 'Department', str(department.id))

    @action(detail=True, methods=['get'])
    def staff_list(self, request, pk=None):
        """Список персонала отделения"""
        department = self.get_object()
        staff = Staff.objects.filter(department=department)
        return Response(StaffSerializer(staff, many=True).data)


# ============ ПРИЁМЫ ============

class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Appointment.objects.all()

    def perform_create(self, serializer):
        appointment = serializer.save()
        log_audit(self.request.user, 'create', 'Appointment', str(appointment.id))

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отмена приема"""
        appointment = self.get_object()
        
        time_until = (
            timezone.make_aware(
                datetime.combine(appointment.appointment_date, appointment.appointment_time)
            ) - timezone.now()
        ).total_seconds() / 3600

        if time_until < 2:
            return Response(
                {'error': 'Невозможно отменить прием менее чем за 2 часа'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = 'cancelled'
        appointment.save()
        log_audit(request.user, 'cancel', 'Appointment', str(appointment.id))
        return Response({'message': 'Прием отменен'})

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Подтверждение приема"""
        appointment = self.get_object()
        appointment.status = 'confirmed'
        appointment.save()
        log_audit(request.user, 'confirm', 'Appointment', str(appointment.id))
        return Response({'message': 'Прием подтвержден'})

    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """Получить свободные слоты врача"""
        doctor_id = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date')

        if not doctor_id or not date_str:
            return Response(
                {'error': 'Требуются параметры doctor_id и date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        doctor = Staff.objects.get(id=doctor_id)
        
        booked = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status__in=['scheduled', 'confirmed']
        ).values_list('appointment_time', flat=True)

        available_slots = []
        for hour in range(9, 17):
            for minute in [0, 30]:
                slot = f"{hour:02d}:{minute:02d}"
                if slot not in [str(t) for t in booked]:
                    available_slots.append(slot)

        return Response({'available_slots': available_slots})


# ============ МЕДИЦИНСКИЕ ЗАПИСИ ============

class MedicalRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]
    queryset = MedicalRecord.objects.all()

    def perform_create(self, serializer):
        record = serializer.save()
        log_audit(self.request.user, 'create', 'MedicalRecord', str(record.id))

    def destroy(self, request, *args, **kwargs):
        """Запрет на удаление медицинских записей"""
        return Response(
            {'error': 'Удаление медицинских записей запрещено'},
            status=status.HTTP_403_FORBIDDEN
        )

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """Электронная подпись врача"""
        record = self.get_object()
        record.is_signed = True
        record.digital_signature = f"Подписано {request.user.get_full_name()} в {timezone.now()}"
        record.save()
        log_audit(request.user, 'sign', 'MedicalRecord', str(record.id))
        return Response({'message': 'Запись подписана'})
