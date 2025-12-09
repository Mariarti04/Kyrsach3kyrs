from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from clinic.views import (
    UserRegistrationView, PatientViewSet, AppointmentViewSet,
    MedicalRecordViewSet, BackupView, ReportView
)

# Создание router для автоматической генерации маршрутов
router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'medical-records', MedicalRecordViewSet, basename='medical-record')
router.register(r'auth', UserRegistrationView, basename='auth')
router.register(r'backup', BackupView, basename='backup')
router.register(r'reports', ReportView, basename='report')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
