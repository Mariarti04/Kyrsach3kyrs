import logging
import hashlib
import json
from datetime import datetime
from .models import AuditLog
from django.utils import timezone
from django.conf import settings
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def log_audit(user, action, model_name, object_id, changes=None, ip_address=None):
    """
    Логирование действий в системе для аудита
    """
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            changes=changes or {},
            ip_address=ip_address,
            timestamp=timezone.now()
        )
    except Exception as e:
        logger.error(f"Ошибка при логировании действия: {str(e)}")


def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class DataEncryption:
    """Класс для шифрования чувствительных данных пациентов"""

    def __init__(self, key=None):
        if key is None:
            key = settings.ENCRYPTION_KEY.encode() if hasattr(settings, 'ENCRYPTION_KEY') else Fernet.generate_key()
        self.cipher = Fernet(key)

    def encrypt(self, data):
        """Шифрование данных"""
        if isinstance(data, str):
            data = data.encode()
        try:
            encrypted = self.cipher.encrypt(data)
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Ошибка при шифровании данных: {str(e)}")
            raise

    def decrypt(self, encrypted_data):
        """Расшифровка данных"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        try:
            decrypted = self.cipher.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Ошибка при расшифровке данных: {str(e)}")
            raise


def encrypt_data(data):
    """Функция для шифрования данных"""
    encryptor = DataEncryption()
    return encryptor.encrypt(data)


def decrypt_data(encrypted_data):
    """Функция для расшифровки данных"""
    encryptor = DataEncryption()
    return encryptor.decrypt(encrypted_data)


def validate_patient_age(date_of_birth):
    """
    Валидация возраста пациента (0-120 лет)
    """
    from datetime import date
    today = date.today()
    age = today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )

    if age < 0 or age > 120:
        raise ValueError(f"Некорректный возраст пациента: {age} лет")

    return age


def validate_insurance_number(insurance_number):
    """
    Валидация номера полиса ОМС
    Формат: 16 цифр
    """
    if not insurance_number.isdigit() or len(insurance_number) != 16:
        raise ValueError(f"Некорректный формат номера полиса: {insurance_number}")
    return insurance_number


def hash_password(password):
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_digital_signature(data, key):
    """
    Генерирование электронной подписи для медицинских документов
    """
    if isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False).encode()
    elif isinstance(data, str):
        data = data.encode()

    signature = hashlib.sha256(data + key.encode()).hexdigest()
    return signature


def check_appointment_conflict(doctor, appointment_date, appointment_time, duration):
    """
    Проверка конфликтов приемов у врача
    Предотвращение пересечения приемов
    """
    from .models import Appointment
    from datetime import datetime, timedelta

    # Комбинируем дату и время
    appointment_datetime = datetime.combine(appointment_date, appointment_time)
    appointment_end = appointment_datetime + timedelta(minutes=duration)

    # Ищем пересекающиеся приемы
    conflicts = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        status__in=['scheduled', 'confirmed']
    )

    for conflict in conflicts:
        conflict_datetime = datetime.combine(
            conflict.appointment_date,
            conflict.appointment_time
        )
        conflict_end = conflict_datetime + timedelta(minutes=conflict.duration_minutes)

        # Проверяем пересечение
        if not (appointment_end <= conflict_datetime or appointment_datetime >= conflict_end):
            return False, f"Конфликт с приемом в {conflict.appointment_time}"

    return True, "Прием возможен"


def auto_cancel_unconfirmed_appointments():
    """
    Периодическая задача (Celery) для автоматической отмены
    неподтвержденных приемов за 24 часа до начала
    """
    from .models import Appointment
    from datetime import timedelta

    threshold = timezone.now() + timedelta(hours=24)

    unconfirmed = Appointment.objects.filter(
        status='scheduled',
        appointment_date__lt=threshold.date()
    )

    for appointment in unconfirmed:
        appointment.status = 'cancelled'
        appointment.save()
        log_audit(None, 'auto_cancel', 'Appointment', str(appointment.id))

    return f"Отменено приемов: {unconfirmed.count()}"


def validate_contact_data(email, phone):
    """
    Валидация контактных данных
    """
    import re

    # Email валидация
    email_pattern = r'^[^@]+@[^@]+\.[^@]+$'
    if email and not re.match(email_pattern, email):
        raise ValueError(f"Некорректный email: {email}")

    # Phone валидация (простая проверка на наличие цифр)
    phone_pattern = r'^\d{10,20}$'
    if phone and not re.match(phone_pattern, phone.replace('+', '').replace('-', '').replace(' ', '')):
        raise ValueError(f"Некорректный номер телефона: {phone}")

    return True
