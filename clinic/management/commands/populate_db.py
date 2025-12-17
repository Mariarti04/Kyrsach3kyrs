from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clinic.models import (
    Patient, Staff, Department, Appointment, 
    MedicalRecord, Diagnosis, InsuranceCompany,
    CustomUser, Prescription
)
from datetime import datetime, timedelta, time, date
from django.utils import timezone
import random
import uuid


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print('=== НАЧИНАЕМ ЗАПОЛНЕНИЕ БД ===\n')

        # ОЧИСТКА
        print('Очистка данных...')
        Prescription.objects.all().delete()
        MedicalRecord.objects.all().delete()
        Appointment.objects.all().delete()
        Patient.objects.all().delete()
        Staff.objects.all().delete()
        Department.objects.all().delete()
        Diagnosis.objects.all().delete()
        InsuranceCompany.objects.all().delete()
        CustomUser.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        print('✓ Очистка завершена\n')

        # 1. СТРАХОВЫЕ КОМПАНИИ
        print('Создаю страховые компании...')
        ic1 = InsuranceCompany.objects.create(
            name='АльфаСтрахование',
            license_number='ЛИЦ-001-2024',
            phone='+7-495-123-45-67',
            email='info@alfains.ru',
            address='г. Москва, ул. Тверская, 1'
        )
        ic2 = InsuranceCompany.objects.create(
            name='ВТБ Страхование',
            license_number='ЛИЦ-002-2024',
            phone='+7-495-234-56-78',
            email='info@vtbins.ru',
            address='г. Москва, пр. Ленина, 5'
        )
        companies = [ic1, ic2]
        print(f'✓ Создано {len(companies)} компаний\n')

        # 2. ДИАГНОЗЫ
        print('Создаю диагнозы...')
        diagnoses = []
        diagnosis_data = [
            ('J06.9', 'ОРВИ'),
            ('I10', 'Гипертония'),
            ('E11', 'Сахарный диабет 2 типа'),
            ('M54.5', 'Боль в пояснице'),
            ('K29.7', 'Гастрит')
        ]
        for code, name in diagnosis_data:
            d = Diagnosis.objects.create(code=code, name=name)
            diagnoses.append(d)
        print(f'✓ Создано {len(diagnoses)} диагнозов\n')

        # 3. ОТДЕЛЕНИЯ
        print('Создаю отделения...')
        d1 = Department.objects.create(
            name='Терапия',
            description='Терапевтическое отделение',
            phone='+7-495-111-11-11',
            cabinet_number='101'
        )
        d2 = Department.objects.create(
            name='Кардиология',
            description='Кардиологическое отделение',
            phone='+7-495-222-22-22',
            cabinet_number='201'
        )
        d3 = Department.objects.create(
            name='Хирургия',
            description='Хирургическое отделение',
            phone='+7-495-333-33-33',
            cabinet_number='301'
        )
        departments = [d1, d2, d3]
        print(f'✓ Создано {len(departments)} отделений\n')

        # 4. ВРАЧИ
        print('Создаю врачей...')
        staff_list = []
        staff_data = [
            ('Иванов Петр Сергеевич', '1975-05-15', 'M', 'doctor', 'Терапия', d1, 'ЛИЦ-Д-001', 20),
            ('Смирнова Анна Викторовна', '1980-03-20', 'F', 'doctor', 'Кардиология', d2, 'ЛИЦ-Д-002', 15),
            ('Козлов Дмитрий Александрович', '1978-07-10', 'M', 'doctor', 'Хирургия', d3, 'ЛИЦ-Д-003', 18),
            ('Новикова Елена Ивановна', '1985-11-25', 'F', 'doctor', 'Терапия', d1, 'ЛИЦ-Д-004', 10),
            ('Морозов Сергей Павлович', '1982-02-14', 'M', 'doctor', 'Кардиология', d2, 'ЛИЦ-Д-005', 12),
            ('Петрова Мария Андреевна', '1990-09-30', 'F', 'nurse', 'Медсестра', d1, 'ЛИЦ-М-001', 5)
        ]

        for i, (name, dob, gender, position, specialty, dept, lic, exp) in enumerate(staff_data, 1):
            user = User.objects.create_user(
                username=f'doctor{i}',
                password='password123',
                first_name=name.split()[1],
                last_name=name.split()[0],
                email=f'doctor{i}@clinic.ru'
            )
            CustomUser.objects.create(user=user, role='doctor')
            
            staff = Staff.objects.create(
                user=user,
                full_name=name,
                date_of_birth=dob,
                gender=gender,
                position=position,
                specialty=specialty,
                license_number=lic,
                experience_years=exp,
                department=dept,
                phone=f'+7-926-{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}',
                email=f'doctor{i}@clinic.ru',
                work_schedule={"Monday": "09:00-17:00", "Tuesday": "09:00-17:00"}
            )
            staff_list.append(staff)
        print(f'✓ Создано {len(staff_list)} сотрудников\n')

        # 5. ПАЦИЕНТЫ
        print('Создаю пациентов...')
        patients = []
        patient_data = [
            ('Алексеев Иван Петрович', '1985-03-15', 'M', '4510 123456'),
            ('Борисова Мария Ивановна', '1990-07-22', 'F', '4510 234567'),
            ('Волков Андрей Сергеевич', '1978-11-30', 'M', '4510 345678'),
            ('Григорьева Елена Александровна', '1995-05-18', 'F', '4510 456789'),
            ('Дмитриев Сергей Владимирович', '1982-09-05', 'M', '4510 567890'),
            ('Егорова Анна Николаевна', '2000-12-10', 'F', '4510 678901'),
            ('Жуков Максим Дмитриевич', '1975-04-25', 'M', '4510 789012'),
            ('Зайцева Ольга Викторовна', '1988-08-14', 'F', '4510 890123'),
            ('Иванова Екатерина Петровна', '1992-02-28', 'F', '4510 901234'),
            ('Козлов Алексей Андреевич', '1980-06-07', 'M', '4510 012345')
        ]

        for i, (name, dob, gender, passport) in enumerate(patient_data, 1):
            user = User.objects.create_user(
                username=f'patient{i}',
                password='password123',
                first_name=name.split()[1],
                last_name=name.split()[0],
                email=f'patient{i}@mail.ru'
            )
            CustomUser.objects.create(user=user, role='patient')
            
            patient = Patient.objects.create(
                user=user,
                full_name=name,
                date_of_birth=dob,
                gender=gender,
                passport_number=passport,
                address=f'г. Москва, ул. Ленина, д. {random.randint(1,100)}',
                phone=f'+7-916-{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}',
                email=f'patient{i}@mail.ru',
                insurance_company=random.choice(companies),
                insurance_number=f'ПОЛ-{random.randint(100000000000,999999999999)}',
                emergency_contact=f'Контакт {i}',
                emergency_phone=f'+7-915-000-00-{i:02d}',
                allergies='Нет',
                chronic_diseases='Нет'
            )
            patients.append(patient)
        print(f'✓ Создано {len(patients)} пациентов\n')

        # 6. ПРИЁМЫ
        print('Создаю приёмы...')
        appointments = []
        doctors = [s for s in staff_list if s.position == 'doctor']
        
        for i in range(20):
            days_offset = random.randint(-10, 10)
            app_date = date.today() + timedelta(days=days_offset)
            app_time = time(random.randint(9, 16), random.choice([0, 30]))
            
            appointment = Appointment.objects.create(
                patient=random.choice(patients),
                doctor=random.choice(doctors),
                appointment_date=app_date,
                appointment_time=app_time,
                reason='Консультация',
                status='completed' if days_offset < 0 else 'scheduled',
                duration_minutes=30
            )
            appointments.append(appointment)
        print(f'✓ Создано {len(appointments)} приёмов\n')

        # 7. МЕДИЦИНСКИЕ ЗАПИСИ
        print('Создаю медицинские записи...')
        records = []
        completed = [a for a in appointments if a.status == 'completed']
        
        for appointment in completed[:10]:
            record = MedicalRecord.objects.create(
                patient=appointment.patient,
                appointment=appointment,
                doctor=appointment.doctor,
                record_date=timezone.make_aware(
                    datetime.combine(appointment.appointment_date, appointment.appointment_time)
                ),
                symptoms='Температура 37.5, общая слабость',
                diagnosis=random.choice(diagnoses),
                treatment_plan='Постельный режим, обильное питье',
                is_signed=True,
                digital_signature=f'Подписано {appointment.doctor.full_name}'
            )
            records.append(record)
        print(f'✓ Создано {len(records)} медицинских записей\n')

        # 8. РЕЦЕПТЫ
        print('Создаю рецепты...')
        prescriptions = []
        
        for record in records[:5]:
            prescription = Prescription.objects.create(
                medical_record=record,
                patient=record.patient,
                doctor=record.doctor,
                medication_name='Парацетамол',
                dosage='500мг',
                frequency='2 раза в день',
                duration_days=7,
                instructions='Принимать после еды',
                valid_until=date.today() + timedelta(days=30)
            )
            prescriptions.append(prescription)
        print(f'✓ Создано {len(prescriptions)} рецептов\n')

        # ИТОГ
        print('\n' + '='*60)
        print('✅ БАЗА ДАННЫХ УСПЕШНО ЗАПОЛНЕНА!')
        print('='*60)
        print(f'📊 Статистика:')
        print(f'   • Страховые компании: {len(companies)}')
        print(f'   • Диагнозы: {len(diagnoses)}')
        print(f'   • Отделения: {len(departments)}')
        print(f'   • Персонал: {len(staff_list)}')
        print(f'   • Пациенты: {len(patients)}')
        print(f'   • Приёмы: {len(appointments)}')
        print(f'   • Медицинские записи: {len(records)}')
        print(f'   • Рецепты: {len(prescriptions)}')
        print('\n🔑 Тестовые данные для входа:')
        print('   Врачи: doctor1/password123, doctor2/password123')
        print('   Пациенты: patient1/password123, patient2/password123')
        print('='*60 + '\n')
