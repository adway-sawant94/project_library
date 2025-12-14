# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Project, Order, CustomProjectRequest, PaymentTransaction, Download, UserProfile

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Project admin interface"""
    list_display = ['title', 'technology', 'price', 'downloads', 'is_active', 'featured', 'created_at']
    list_filter = ['technology', 'is_active', 'featured', 'created_at']
    search_fields = ['title', 'short_description', 'technology']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_active', 'featured', 'price']
    readonly_fields = ['downloads', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'short_description', 'long_description')
        }),
        ('Technical Details', {
            'fields': ('technology', 'price', 'image', 'demo_video_link', 'project_file')
        }),
        ('Settings', {
            'fields': ('is_active', 'featured')
        }),
        ('Statistics', {
            'fields': ('downloads', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # New project
            obj.downloads = 0
            obj.save()

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order admin interface"""
    list_display = ['order_id', 'user', 'project', 'amount', 'status', 'created_at', 'payment_id_display']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'user__username', 'project__title', 'razorpay_payment_id']
    readonly_fields = ['order_id', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at']
    list_per_page = 50
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'project', 'amount', 'status')
        }),
        ('Payment Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def payment_id_display(self, obj):
        if obj.razorpay_payment_id:
            return format_html('<span style="color: green;">✓ {}</span>', obj.razorpay_payment_id[:20])
        return format_html('<span style="color: red;">Not Paid</span>')
    payment_id_display.short_description = 'Payment ID'

@admin.register(CustomProjectRequest)
class CustomProjectRequestAdmin(admin.ModelAdmin):
    """Custom project request admin interface"""
    list_display = ['name', 'email', 'project_type', 'budget', 'deadline', 'status', 'created_at']
    list_filter = ['status', 'project_type', 'created_at']
    search_fields = ['name', 'email', 'phone', 'description']
    list_editable = ['status']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Client Information', {
            'fields': ('name', 'email', 'phone', 'user')
        }),
        ('Project Details', {
            'fields': ('project_type', 'deadline', 'description', 'budget')
        }),
        ('Status & Notes', {
            'fields': ('status', 'admin_notes')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_in_progress', 'mark_completed']
    
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} requests marked as in progress.')
    mark_in_progress.short_description = 'Mark selected as In Progress'
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} requests marked as completed.')
    mark_completed.short_description = 'Mark selected as Completed'

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Payment transaction admin interface"""
    list_display = ['transaction_id', 'order', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['transaction_id', 'order__order_id']
    readonly_fields = ['transaction_id', 'order', 'amount', 'currency', 'payment_method', 'status', 'razorpay_response', 'created_at']
    
    def has_add_permission(self, request):
        return False

@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    """Download tracking admin interface"""
    list_display = ['user', 'project', 'order', 'downloaded_at', 'ip_address']
    list_filter = ['downloaded_at']
    search_fields = ['user__username', 'project__title', 'order__order_id']
    readonly_fields = ['user', 'project', 'order', 'downloaded_at', 'ip_address']
    
    def has_add_permission(self, request):
        return False

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User profile admin interface"""
    list_display = ['user', 'phone', 'college', 'course', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'college']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Profile Information', {
            'fields': ('phone', 'college', 'course')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )