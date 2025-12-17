from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clinic.models import Patient, Staff, Department, Appointment
from datetime import date, time, timedelta
import random


class Command(BaseCommand):
    help = 'Загружает тестовые данные в базу'

    def handle(self, *args, **kwargs):
        self.stdout.write('Загрузка тестовых данных...')
        
        # Создаем отделения
        departments = []
        dept_names = ['Терапия', 'Хирургия', 'Кардиология', 'Неврология']
        for name in dept_names:
            dept, _ = Department.objects.get_or_create(
                name=name,
                defaults={'description': f'Отделение {name}'}
            )
            departments.append(dept)
        
        # Создаем врачей
        doctors = []
        doctor_data = [
            ('Иванов Иван Иванович', 'Терапевт', 15),
            ('Петров Петр Петрович', 'Хирург', 20),
            ('Сидорова Анна Сергеевна', 'Кардиолог', 12),
            ('Смирнов Алексей Викторович', 'Невролог', 8),
        ]
        
        for idx, (name, specialty, exp) in enumerate(doctor_data):
            username = f'doctor{idx+1}'
            
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password='doctor123')
            else:
                user = User.objects.get(username=username)
            
            if not Staff.objects.filter(user=user).exists():
                staff = Staff.objects.create(
                    user=user,
                    full_name=name,
                    date_of_birth=date(1980 + idx, 1, 1),
                    gender='M' if idx % 2 == 0 else 'F',
                    position='doctor',
                    specialty=specialty,
                    experience_years=exp,
                    phone=f'+7999555{idx:04d}',
                    department=departments[idx]
                )
                doctors.append(staff)
        
        # Создаем пациентов
        patients = []
        patient_data = [
            ('Александров Александр', 'M', '1985-05-15'),
            ('Борисова Мария', 'F', '1990-08-20'),
            ('Васильев Сергей', 'M', '1975-03-10'),
            ('Григорьева Елена', 'F', '1988-11-25'),
            ('Дмитриев Дмитрий', 'M', '1995-07-30'),
            ('Егорова Ольга', 'F', '1982-12-05'),
        ]
        
        for idx, (name, gender, birth) in enumerate(patient_data):
            if not Patient.objects.filter(full_name=name).exists():
                patient = Patient.objects.create(
                    full_name=name,
                    date_of_birth=birth,
                    gender=gender,
                    phone=f'+7999111{idx:04d}',
                    email=f'patient{idx}@test.com',
                    address=f'г. Москва, ул. Тестовая, д. {idx+1}'
                )
                patients.append(patient)
        
        if not patients:
            patients = list(Patient.objects.all()[:6])
        
        if not doctors:
            doctors = list(Staff.objects.filter(position='doctor')[:4])
        
        # Создаем приемы
        if patients and doctors:
            today = date.today()
            for i in range(10):
                Appointment.objects.get_or_create(
                    patient=random.choice(patients),
                    doctor=random.choice(doctors),
                    appointment_date=today + timedelta(days=random.randint(-30, 30)),
                    appointment_time=time(random.randint(9, 17), 0),
                    defaults={
                        'status': random.choice(['scheduled', 'confirmed']),
                        'reason': 'Консультация'
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('Тестовые данные загружены!'))
        self.stdout.write(f'Пациентов: {Patient.objects.count()}')
        self.stdout.write(f'Врачей: {Staff.objects.filter(position="doctor").count()}')
        self.stdout.write(f'Отделений: {Department.objects.count()}')
