# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
import razorpay
import hmac
import hashlib
import json

from .models import Project, Order, CustomProjectRequest, PaymentTransaction, Download, UserProfile
from .forms import CustomProjectRequestForm, UserRegistrationForm, UserProfileForm

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Home Page
def home_view(request):
    """Home page with featured projects"""
    featured_projects = Project.objects.filter(is_active=True, featured=True)[:6]
    recent_projects = Project.objects.filter(is_active=True).order_by('-created_at')[:8]
    context = {
        'featured_projects': featured_projects,
        'recent_projects': recent_projects,
    }
    return render(request, 'home.html', context)

# Project Listing
def project_list_view(request):
    """List all projects with search and filter"""
    projects = Project.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) | 
            Q(short_description__icontains=search_query) |
            Q(technology__icontains=search_query)
        )
    
    # Filter by technology
    technology = request.GET.get('technology', '')
    if technology:
        projects = projects.filter(technology=technology)
    
    # Pagination
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    technologies = Project.TECHNOLOGY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'technologies': technologies,
        'search_query': search_query,
        'selected_technology': technology,
    }
    return render(request, 'projects/project_list.html', context)

# Project Detail
def project_detail_view(request, slug):
    """Detailed view of a single project"""
    project = get_object_or_404(Project, slug=slug, is_active=True)
    
    # Check if user has already purchased
    has_purchased = False
    if request.user.is_authenticated:
        has_purchased = Order.objects.filter(
            user=request.user,
            project=project,
            status='completed'
        ).exists()
    
    related_projects = Project.objects.filter(
        technology=project.technology,
        is_active=True
    ).exclude(id=project.id)[:4]
    
    context = {
        'project': project,
        'has_purchased': has_purchased,
        'related_projects': related_projects,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'projects/project_detail.html', context)

# Create Razorpay Order
@login_required
def create_order(request, project_id):
    """Create Razorpay order"""
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id, is_active=True)
        
        # Check if already purchased
        existing_order = Order.objects.filter(
            user=request.user,
            project=project,
            status='completed'
        ).first()
        
        if existing_order:
            return JsonResponse({'error': 'You have already purchased this project'}, status=400)
        
        try:
            # Create Razorpay order
            amount = int(float(project.price) * 100)  # Convert to paise
            razorpay_order = razorpay_client.order.create({
                'amount': amount,
                'currency': 'INR',
                'payment_capture': 1
            })
            
            # Create order in database
            order = Order.objects.create(
                user=request.user,
                project=project,
                amount=project.price,
                razorpay_order_id=razorpay_order['id']
            )
            
            return JsonResponse({
                'order_id': razorpay_order['id'],
                'amount': amount,
                'currency': 'INR',
                'name': project.title,
                'key': settings.RAZORPAY_KEY_ID,
                'db_order_id': order.order_id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Verify Payment
@csrf_exempt
def verify_payment(request):
    """Verify Razorpay payment"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_signature = data.get('razorpay_signature')
            
            # Verify signature
            generated_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            if generated_signature == razorpay_signature:
                # Update order
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                order.razorpay_payment_id = razorpay_payment_id
                order.razorpay_signature = razorpay_signature
                order.status = 'completed'
                order.save()
                
                # Create transaction log
                PaymentTransaction.objects.create(
                    transaction_id=razorpay_payment_id,
                    order=order,
                    amount=order.amount,
                    status='success',
                    razorpay_response=data
                )
                
                # Update project downloads count
                order.project.downloads += 1
                order.project.save()
                
                # Send confirmation email
                send_purchase_confirmation_email(order)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Payment verified successfully',
                    'order_id': order.order_id
                })
            else:
                return JsonResponse({'status': 'failed', 'message': 'Signature verification failed'}, status=400)
                
        except Order.DoesNotExist:
            return JsonResponse({'status': 'failed', 'message': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Payment Success
@login_required
def payment_success(request):
    """Payment success page"""
    order_id = request.GET.get('order_id')
    order = None
    if order_id:
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'payments/success.html', {'order': order})

# Payment Failed
def payment_failed(request):
    """Payment failed page"""
    return render(request, 'payments/failed.html')

# Download Project
@login_required
def download_project(request, order_id):
    """Download purchased project"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user, status='completed')
    
    # Create download record
    Download.objects.create(
        user=request.user,
        project=order.project,
        order=order,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Serve file
    file_path = order.project.project_file.path
    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    return response

# User Dashboard
@login_required
def dashboard_view(request):
    """User dashboard showing purchased projects"""
    orders = Order.objects.filter(user=request.user, status='completed').select_related('project')
    context = {
        'orders': orders,
    }
    return render(request, 'dashboard/dashboard.html', context)

# Custom Project Request
def custom_project_request_view(request):
    """Custom project request form"""
    if request.method == 'POST':
        form = CustomProjectRequestForm(request.POST)
        if form.is_valid():
            custom_request = form.save(commit=False)
            if request.user.is_authenticated:
                custom_request.user = request.user
            custom_request.save()
            
            # Send notification email to admin
            send_custom_request_notification(custom_request)
            
            messages.success(request, 'Your request has been submitted successfully! We will contact you soon.')
            return redirect('core:home')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name(),
                'email': request.user.email,
            }
        form = CustomProjectRequestForm(initial=initial_data)
    
    return render(request, 'custom_request.html', {'form': form})

# User Registration
def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to our platform.')
            return redirect('core:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})

# User Login
def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'auth/login.html')

# User Logout
def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')

# Helper Functions
def send_purchase_confirmation_email(order):
    """Send purchase confirmation email"""
    subject = f'Purchase Confirmation - {order.project.title}'
    message = f"""
    Dear {order.user.get_full_name() or order.user.username},
    
     Thank you for your purchase from ProjectLibrary!
    
    Order Details:
    - Order ID: {order.order_id}
    - Project: {order.project.title}
    - Amount: ₹{order.amount}
    
    You can download your project from your dashboard.
    
     Thank you for choosing ProjectLibrary!
    
    Best regards,
    ProjectLibrary Team 
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.user.email])
    except Exception as e:
        print(f"Email error: {e}")

def send_custom_request_notification(custom_request):
    """Send custom request notification to admin"""
    subject = f'New Custom Project Request - {custom_request.project_type}'
    message = f"""
    New custom project request received:
    
    Name: {custom_request.name}
    Email: {custom_request.email}
    Phone: {custom_request.phone}
    Project Type: {custom_request.project_type}
    Deadline: {custom_request.deadline}
    Budget: ₹{custom_request.budget}
    
    Description:
    {custom_request.description}
    
    ProjectLibrary System
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
    except Exception as e:
        print(f"Email error: {e}")

# Static Pages
def terms_view(request):
    """Terms and conditions page"""
    return render(request, 'static/terms.html')

def privacy_view(request):
    """Privacy policy page"""
    return render(request, 'static/privacy.html')
