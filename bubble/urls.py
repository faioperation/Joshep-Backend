from django.contrib import admin
from django.urls import path,include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Spartacus Bubble AI - API Ecosystem",
      default_version='v1',
      description="Professional API documentation for the fully automated AI Booking and Support system.",
      contact=openapi.Contact(email="support@fireai.agency"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
     path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'), # এই ইউআরএল-এ সব ডকুমেন্টেশন 
    path('api-auth/', include('rest_framework.urls')),
    path('user/', include('users.urls')),
    path('api/booking/', include('bookinge.urls')),
    path('api/support/', include('support.urls')),
    path('api/dashboards/', include('Dashboards.urls')),
    path('', include('Test.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

