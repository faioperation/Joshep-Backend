from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import rezgo_webhook_receiver, DashboardStatsView, FAQViewSet, LocationMappingViewSet

router = DefaultRouter()
router.register(r'faqs', FAQViewSet, basename='faqs')
router.register(r'locations', LocationMappingViewSet, basename='locations')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('webhook/rezgo/', rezgo_webhook_receiver, name='rezgo-webhook'),
]