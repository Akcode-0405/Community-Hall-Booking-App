"""
URL patterns for bookings app.
"""
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.BookingListCreateView.as_view(), name='booking-list-create'),
    path('<uuid:id>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('<uuid:id>/approve/', views.BookingApproveView.as_view(), name='booking-approve'),
    path('<uuid:id>/reject/', views.BookingRejectView.as_view(), name='booking-reject'),
    path('<uuid:id>/cancel/', views.BookingCancelView.as_view(), name='booking-cancel'),
]
