from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public routes
    path('', views.home, name='home'),
    path('track/', views.track_shipment, name='track_shipment'),
    path('upload-proof/<str:tracking_number>/', views.upload_payment_proof, name='upload_proof'),
    path('print-preview/<str:tracking_number>/', views.print_preview, name='print_preview'),
    path('print/<str:tracking_number>/', views.print_tracking_pdf, name='print_pdf'),
    
    # Admin Authentication routes - CHANGED FROM 'admin/login/' TO 'auth/login/'
    path('auth/login/', auth_views.LoginView.as_view(template_name='tracker/admin/login.html'), name='admin_login'),
    path('auth/logout/', auth_views.LogoutView.as_view(next_page='home'), name='admin_logout'),
    
    # Admin dashboard routes - PROTECTED
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/shipments/', views.admin_shipments, name='admin_shipments'),
    path('dashboard/shipments/create/', views.admin_create_shipment, name='admin_create_shipment'),
    path('dashboard/shipments/edit/<int:shipment_id>/', views.admin_edit_shipment, name='admin_edit_shipment'),
    path('dashboard/shipments/delete/<int:shipment_id>/', views.admin_delete_shipment, name='admin_delete_shipment'),
    path('dashboard/payments/', views.admin_payments, name='admin_payments'),
    path('dashboard/verify-payment/<int:proof_id>/', views.verify_payment, name='verify_payment'),
    path('dashboard/reject-payment/<int:proof_id>/', views.reject_payment, name='reject_payment'),
    path('dashboard/stats/', views.admin_stats, name='admin_stats'),
    path('dashboard/settings/', views.admin_settings, name='admin_settings'),
]