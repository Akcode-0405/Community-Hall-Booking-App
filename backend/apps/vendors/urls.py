"""
URL patterns for vendors app.
"""
from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    # Public
    path('', views.PublicVendorListView.as_view(), name='public-vendor-list'),
    path('categories/', views.VendorCategoryListView.as_view(), name='category-list'),
    path('<uuid:id>/', views.PublicVendorDetailView.as_view(), name='public-vendor-detail'),

    # Vendor management
    path('me/', views.MyVendorProfileView.as_view(), name='vendor-profile-short'),
    path('me/profile/', views.MyVendorProfileView.as_view(), name='vendor-my-profile'),
    path('services/', views.MyVendorServiceListCreateView.as_view(), name='vendor-services-short'),
    path('services/<uuid:id>/', views.MyVendorServiceDetailView.as_view(), name='vendor-service-detail-short'),
    path('me/services/', views.MyVendorServiceListCreateView.as_view(), name='vendor-my-services'),
    path('me/services/<uuid:id>/', views.MyVendorServiceDetailView.as_view(), name='vendor-my-service-detail'),
    path('bookings/', views.VendorBookingsView.as_view(), name='vendor-bookings'),
    path('bookings/<uuid:id>/respond/', views.VendorBookingRespondView.as_view(), name='vendor-booking-respond'),
]
