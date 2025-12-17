from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from clinic.views import (
    PatientViewSet, 
    StaffViewSet,
    AppointmentViewSet,
    DepartmentViewSet,
    MedicalRecordViewSet,
)

# Swagger
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Medical Clinic API",
      default_version='v1',
      description="API для управления медицинской клиникой",
      contact=openapi.Contact(email="admin@clinic.ru"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Router
router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'medical-records', MedicalRecordViewSet, basename='medical-record')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    
    # Документация API
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
