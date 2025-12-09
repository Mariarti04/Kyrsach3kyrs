from rest_framework.permissions import BasePermission


class IsPatient(BasePermission):
    """Доступ только для пациентов"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'customuser') and
            request.user.customuser.role == 'patient'
        )


class IsDoctor(BasePermission):
    """Доступ только для врачей"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'customuser') and
            request.user.customuser.role == 'doctor'
        )


class IsNurse(BasePermission):
    """Доступ только для медсестер"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'customuser') and
            request.user.customuser.role == 'nurse'
        )


class IsRegistrar(BasePermission):
    """Доступ только для регистраторов"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'customuser') and
            request.user.customuser.role == 'registrar'
        )


class IsAdmin(BasePermission):
    """Доступ только для администраторов"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'customuser') and
            request.user.customuser.role == 'admin'
        )


class IsStaff(BasePermission):
    """Доступ для медицинского персонала (врач, медсестра)"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'customuser') and
            request.user.customuser.role in ['doctor', 'nurse', 'registrar', 'admin']
        )
