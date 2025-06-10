from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'stock'

urlpatterns = [
    # Landing Page
    path('', views.LandingView.as_view(), name='landing'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='stock:login'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='stock/password_reset.html',
             email_template_name='stock/password_reset_email.html',
             subject_template_name='stock/password_reset_subject.txt',
             success_url='stock:password_reset_done'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='stock/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='stock/password_reset_confirm.html',
             success_url='stock:password_reset_complete'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='stock/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Product Management URLs
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Category Management URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Suppliers
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/update/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),

    # Stock Control
    path('stock/adjust/', views.StockAdjustmentView.as_view(), name='stock_adjustment'),
    path('stock/history/', views.StockHistoryView.as_view(), name='stock_history'),

    # Sales Management
    path('sales/', views.SaleListView.as_view(), name='sale_list'),
    path('sales/new/', views.SaleCreateView.as_view(), name='new_sale'),
    path('sales/<int:pk>/', views.SaleDetailView.as_view(), name='sale_detail'),
    path('sales/analytics/', views.SalesAnalyticsView.as_view(), name='sales_analytics'),

    # Reports
    path('reports/', views.ReportsView.as_view(), name='reports'),

    # Stock Alerts
    path('stock/alerts/', views.StockAlertsView.as_view(), name='stock_alerts'),

    # Settings
    path('settings/', views.SettingsView.as_view(), name='settings'),
] 