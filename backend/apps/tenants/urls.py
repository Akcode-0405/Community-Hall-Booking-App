"""
URL configuration for the tenants app.
"""
from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('', views.TenantListView.as_view(), name='tenant-list'),
    path('current/', views.CurrentTenantView.as_view(), name='tenant-current'),
    path('<uuid:id>/', views.TenantDetailView.as_view(), name='tenant-detail'),
    path('<uuid:id>/suspend/', views.TenantSuspendView.as_view(), name='tenant-suspend'),
    path('<uuid:id>/activate/', views.TenantActivateView.as_view(), name='tenant-activate'),
]
