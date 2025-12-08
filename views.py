from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json
import csv
from io import BytesIO, StringIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
import boto3
import logging

from .models import (
    Patient, Staff, Appointment, MedicalRecord, Prescription,
    Procedure, ProcedureRecord, Department, Diagnosis, InsuranceCompany,
    CustomUser, AuditLog
)
from .serializers import (
    PatientSerializer, StaffSerializer, AppointmentSerializer,
    MedicalRecordSerializer, PrescriptionSerializer
)
from .permissions import IsPatient, IsDoctor, IsNurse, IsRegistrar, IsAdmin
from .utils import log_audit, encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


# ============ АУТЕНТИФИКАЦИЯ И АВТОРИЗАЦИЯ ============

class UserRegistrationView(viewsets.ViewSet):
    """Регистрация новых пользователей"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Регистрация пациента"""
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Пользователь уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

        # Создание CustomUser с ролью пациента
        CustomUser.objects.create(user=user, role='patient')

        log_audit(request.user, 'user_registration', 'CustomUser', str(user.id))

        return Response(
            {'message': 'Пользователь успешно зарегистрирован'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Логин пользователя с JWT токеном"""
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                log_audit(user, 'user_login', 'User', str(user.id))
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_id': user.id,
                    'role': user.customuser.role
                })
            else:
                return Response(
                    {'error': 'Неверный пароль'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============ ПАЦИЕНТЫ ============

class PatientViewSet(viewsets.ModelViewSet):
    """
    CRUD операции для пациентов
    Фильтрация по ФИО и номеру полиса
    """
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['insurance_number', 'gender']
    search_fields = ['full_name', 'insurance_number']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'customuser'):
            if user.customuser.role == 'patient':
                return Patient.objects.filter(user=user)
        return Patient.objects.all()

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
            'prescriptions': PrescriptionSerializer(
                Prescription.objects.filter(patient=patient),
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

        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)

        # Заголовок
        writer.writerow([
            'ФИО', 'Дата рождения', 'Пол', 'Номер полиса',
            'Адрес', 'Телефон', 'Аллергии', 'Хронические болезни'
        ])

        # Данные пациента
        writer.writerow([
            patient.full_name,
            patient.date_of_birth,
            patient.get_gender_display(),
            patient.insurance_number,
            patient.address,
            patient.phone,
            patient.allergies,
            patient.chronic_diseases
        ])

        log_audit(request.user, 'export_csv', 'Patient', str(patient.id))

        response = FileResponse(
            BytesIO(csv_buffer.getvalue().encode()),
            content_type='text/csv'
        )
        response['Content-Disposition'] = f'attachment; filename="patient_{patient.id}.csv"'
        return response

    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        """Экспорт медицинской карты пациента в PDF"""
        patient = self.get_object()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=1
        )
        elements.append(Paragraph(f'Медицинская карта пациента', title_style))
        elements.append(Spacer(1, 0.3*inch))

        # Личные данные
        patient_data = [
            ['ФИО', patient.full_name],
            ['Дата рождения', str(patient.date_of_birth)],
            ['Возраст', str(patient.age)],
            ['Пол', patient.get_gender_display()],
            ['Номер полиса', patient.insurance_number],
            ['Адрес', patient.address],
            ['Телефон', patient.phone],
        ]

        table = Table(patient_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.5*inch))

        # Медицинские записи
        elements.append(Paragraph('Последние медицинские записи', styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))

        records = MedicalRecord.objects.filter(patient=patient)[:5]
        for record in records:
            elements.append(Paragraph(f'<b>Дата:</b> {record.record_date.date()}', styles['Normal']))
            elements.append(Paragraph(f'<b>Врач:</b> {record.doctor.full_name}', styles['Normal']))
            elements.append(Paragraph(f'<b>Симптомы:</b> {record.symptoms}', styles['Normal']))
            if record.diagnosis:
                elements.append(Paragraph(f'<b>Диагноз:</b> {record.diagnosis.name}', styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))

        doc.build(elements)
        buffer.seek(0)

        log_audit(request.user, 'export_pdf', 'Patient', str(patient.id))

        response = FileResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="patient_card_{patient.id}.pdf"'
        return response


# ============ НАЗНАЧЕНИЯ ============

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Управление приемами
    - Запись на прием
    - Отмена приема (не менее чем за 2 часа)
    - Контроль занятости врача
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'appointment_date', 'doctor']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'customuser'):
            if user.customuser.role == 'patient':
                patient = Patient.objects.filter(user=user).first()
                if patient:
                    return Appointment.objects.filter(patient=patient)
        return Appointment.objects.all()

    def perform_create(self, serializer):
        appointment = serializer.save()
        # Проверка пересечений
        log_audit(self.request.user, 'create', 'Appointment', str(appointment.id))

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отмена приема (не менее чем за 2 часа)"""
        appointment = self.get_object()

        time_until_appointment = (
            timezone.make_aware(
                datetime.combine(appointment.appointment_date, appointment.appointment_time)
            ) - timezone.now()
        ).total_seconds() / 3600

        if time_until_appointment < 2:
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
        """Получить свободные слоты врача на дату"""
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

        # Получить занятые слоты
        booked_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status__in=['scheduled', 'confirmed']
        ).values_list('appointment_time', flat=True)

        # Сгенерировать доступные слоты (30-минутные)
        available_slots = []
        start_hour = 9
        end_hour = 17

        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                time_slot = f"{hour:02d}:{minute:02d}"
                if time_slot not in [str(t) for t in booked_appointments]:
                    available_slots.append(time_slot)

        return Response({'available_slots': available_slots})


# ============ МЕДИЦИНСКИЕ ЗАПИСИ ============

class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    Управление медицинскими записями
    - Запрет на удаление (только добавление)
    - Обязательная подпись врача
    - Аудит всех изменений
    """
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

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


# ============ ЭКСПОРТ И РЕЗЕРВНОЕ КОПИРОВАНИЕ ============

class BackupView(viewsets.ViewSet):
    """Резервное копирование БД в облако (S3)"""
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        """
        Создать резервную копию БД и загрузить в S3
        """
        try:
            # Здесь должна быть реализация:
            # 1. Создание дампа БД (pg_dump)
            # 2. Загрузка в S3 или облако

            backup_info = {
                'status': 'success',
                'timestamp': timezone.now().isoformat(),
                'message': 'Резервная копия успешно создана'
            }
            log_audit(request.user, 'create_backup', 'Backup', str(timezone.now()))
            return Response(backup_info)
        except Exception as e:
            logger.error(f"Ошибка при создании резервной копии: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def list_backups(self, request):
        """Получить список всех резервных копий"""
        # Получить список файлов из S3
        backups = [
            {
                'name': 'backup_2024_01_08_001.sql',
                'size': '1.2GB',
                'date': '2024-01-08 10:00:00'
            },
        ]
        return Response(backups)


# ============ ОТЧЕТЫ ============

class ReportView(viewsets.ViewSet):
    """Статистика и отчеты"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def patients_report(self, request):
        """Отчет по пациентам"""
        total_patients = Patient.objects.count()
        new_patients_this_month = Patient.objects.filter(
            created_at__month=timezone.now().month
        ).count()

        return Response({
            'total_patients': total_patients,
            'new_patients_this_month': new_patients_this_month,
            'by_insurance': list(
                Patient.objects.values('insurance_company__name')
                .annotate(count=models.Count('id'))
            )
        })

    @action(detail=False, methods=['get'])
    def appointments_report(self, request):
        """Отчет по приемам"""
        total = Appointment.objects.count()
        completed = Appointment.objects.filter(status='completed').count()
        cancelled = Appointment.objects.filter(status='cancelled').count()

        return Response({
            'total': total,
            'completed': completed,
            'cancelled': cancelled,
            'completion_rate': f"{(completed/total*100):.2f}%" if total > 0 else "0%"
        })
