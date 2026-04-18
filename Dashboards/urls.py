from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RezgoWebhookReceiver, DashboardStatsView, FAQViewSet, LocationMappingViewSet

router = DefaultRouter()
router.register(r'faqs', FAQViewSet, basename='faqs')
router.register(r'locations', LocationMappingViewSet, basename='locations')

urlpatterns = [
    # এটি দিলে আপনি পাবেন: GET/POST/PUT/DELETE /api/dashboards/faqs/
    path('', include(router.urls)), 
    
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('webhook/rezgo/', RezgoWebhookReceiver.as_view(), name='rezgo-webhook'),
]