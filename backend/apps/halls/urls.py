"""
URL patterns for halls, locations, amenities, and discovery.
"""
from django.urls import path
from . import views

app_name = 'halls'

urlpatterns = [
    # Public discovery
    path('', views.PublicHallListView.as_view(), name='public-hall-list'),
    path('amenities/', views.AmenityListView.as_view(), name='amenity-list'),
    path('compare/', views.CompareHallsView.as_view(), name='compare-halls'),
    path('<uuid:id>/', views.PublicHallDetailView.as_view(), name='public-hall-detail'),
    path('<uuid:hall_id>/availability/', views.HallAvailabilityView.as_view(), name='hall-availability'),

    # Tenant management
    path('manage/locations/', views.LocationListCreateView.as_view(), name='tenant-location-list'),
    path('manage/locations/<uuid:id>/', views.LocationDetailView.as_view(), name='tenant-location-detail'),
    path('manage/halls/', views.TenantHallListCreateView.as_view(), name='tenant-hall-list'),
    path('manage/halls/<uuid:id>/', views.TenantHallDetailView.as_view(), name='tenant-hall-detail'),
]

