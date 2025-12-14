"""
URL Configuration for the core app
All app-specific URLs are defined here with namespace 'core'
"""

from django.urls import path
from . import views

# App namespace for URL reversing
app_name = 'core'

urlpatterns = [
    # ========== HOME ==========
    path('', views.home_view, name='home'),
    
    # ========== PROJECTS ==========
    # List all projects with search and filter
    path('projects/', views.project_list_view, name='project_list'),
    
    # Individual project detail page
    path('projects/<slug:slug>/', views.project_detail_view, name='project_detail'),
    
    # ========== PAYMENTS ==========
    # Create Razorpay order (AJAX endpoint)
    path('create-order/<int:project_id>/', views.create_order, name='create_order'),
    
    # Verify payment after Razorpay success (AJAX endpoint)
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    
    # Payment result pages
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    
    # ========== DOWNLOADS ==========
    # Download purchased project file
    path('download/<str:order_id>/', views.download_project, name='download_project'),
    
    # ========== USER DASHBOARD ==========
    # User dashboard showing purchased projects
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # ========== CUSTOM PROJECT REQUESTS ==========
    # Custom project request form
    path('custom-request/', views.custom_project_request_view, name='custom_request'),
    
    # ========== AUTHENTICATION ==========
    # User registration
    path('register/', views.register_view, name='register'),
    
    # User login
    path('login/', views.login_view, name='login'),
    
    # User logout
    path('logout/', views.logout_view, name='logout'),
    
    # ========== STATIC PAGES ==========
    # Terms and conditions
    path('terms/', views.terms_view, name='terms'),
    
    # Privacy policy
    path('privacy/', views.privacy_view, name='privacy'),
]

