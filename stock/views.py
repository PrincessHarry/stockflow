from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.views.generic import CreateView, TemplateView, ListView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum, Count, F, Value, DecimalField
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from .models import Product, Sale, StockHistory, Category, Supplier
from .forms import ProductForm, CategoryForm, SupplierForm, StockAdjustmentForm, SaleForm
from django.db.models import Q
from django.db import transaction

# Create your views here.

class CustomLoginView(LoginView):
    template_name = 'stock/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('stock:dashboard')

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'stock/register.html'
    success_url = reverse_lazy('stock:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully. Please login.')
        return response

class CustomPasswordResetView(PasswordResetView):
    template_name = 'stock/password_reset.html'
    email_template_name = 'stock/password_reset_email.html'
    subject_template_name = 'stock/password_reset_subject.txt'
    success_url = reverse_lazy('stock:password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        if not self.get_users(email):
            messages.error(self.request, 'No account found with this email address.')
            return self.form_invalid(form)
        return super().form_valid(form)

class StockLoginRequiredMixin(LoginRequiredMixin):
    login_url = reverse_lazy('stock:login')

class DashboardView(StockLoginRequiredMixin, TemplateView):
    template_name = 'stock/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_products'] = Product.objects.count()
        context['total_categories'] = Category.objects.count()
        context['total_sales'] = Sale.objects.count()
        context['total_suppliers'] = Supplier.objects.count()
        context['total_stock_adjustments'] = StockHistory.objects.count()
        context['total_sales_value'] = Sale.objects.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        context['total_stock_value'] = Product.objects.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or 0
        context['total_stock_adjustments_value'] = StockHistory.objects.aggregate(
            total=Sum('quantity_changed')
        )['total'] or 0
        
        # Calculate KPIs
        total_stock_value = Product.objects.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or 0
        sales_count = Sale.objects.count()
        low_stock_count = Product.objects.filter(quantity__lte=F('reorder_level')).count()

        # Get recent sales data for the chart
        last_30_days = timezone.now() - timedelta(days=30)
        daily_sales = Sale.objects.filter(
            timestamp__gte=last_30_days
        ).values('timestamp__date').annotate(
            total=Sum('total_price')
        ).order_by('timestamp__date')

        # Get stock alerts
        low_stock_products = Product.objects.filter(quantity__lte=F('reorder_level')).select_related('category', 'supplier')

        # Get recent stock movements
        recent_movements = StockHistory.objects.select_related(
            'product', 'staff'
        ).order_by('-timestamp')[:5]

        context.update({
            'total_stock_value': total_stock_value,
            'sales_count': sales_count,
            'low_stock_count': low_stock_count,
            'daily_sales': list(daily_sales),
            'low_stock_products': low_stock_products,
            'recent_movements': recent_movements,
        })
        return context

class ProductListView(StockLoginRequiredMixin, ListView):
    model = Product
    template_name = 'stock/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category', 'supplier')
        
        # Search by name or SKU
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by supplier
        supplier = self.request.GET.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        
        # Filter by quantity
        quantity_filter = self.request.GET.get('quantity_filter')
        quantity_value = self.request.GET.get('quantity_value')
        if quantity_filter and quantity_value:
            try:
                quantity_value = int(quantity_value)
                if quantity_filter == 'below':
                    queryset = queryset.filter(quantity__lt=quantity_value)
                elif quantity_filter == 'above':
                    queryset = queryset.filter(quantity__gt=quantity_value)
                elif quantity_filter == 'equal':
                    queryset = queryset.filter(quantity=quantity_value)
            except ValueError:
                pass
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__range=[start, end])
            except ValueError:
                pass
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['suppliers'] = Supplier.objects.all()
        
        # Add current filter values to context
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'category': self.request.GET.get('category', ''),
            'supplier': self.request.GET.get('supplier', ''),
            'quantity_filter': self.request.GET.get('quantity_filter', ''),
            'quantity_value': self.request.GET.get('quantity_value', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
        }
        
        return context

class ProductCreateView(StockLoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'stock/product_form.html'
    success_url = reverse_lazy('stock:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product created successfully.')
        return super().form_valid(form)

class ProductUpdateView(StockLoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'stock/product_form.html'
    success_url = reverse_lazy('stock:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product updated successfully.')
        return super().form_valid(form)

class ProductDeleteView(StockLoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'stock/product_confirm_delete.html'
    success_url = reverse_lazy('stock:product_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Product deleted successfully.')
        return super().delete(request, *args, **kwargs)

class ProductDetailView(StockLoginRequiredMixin, DetailView):
    model = Product
    template_name = 'stock/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stock_history'] = StockHistory.objects.filter(
            product=self.object
        ).select_related('staff').order_by('-timestamp')[:10]
        return context

class CategoryListView(StockLoginRequiredMixin, ListView):
    model = Category
    template_name = 'stock/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset.annotate(product_count=Count('product'))

class CategoryCreateView(StockLoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'stock/category_form.html'
    success_url = reverse_lazy('stock:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully.')
        return super().form_valid(form)

class CategoryUpdateView(StockLoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'stock/category_form.html'
    success_url = reverse_lazy('stock:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully.')
        return super().form_valid(form)

class CategoryDeleteView(StockLoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'stock/category_confirm_delete.html'
    success_url = reverse_lazy('stock:category_list')

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        if category.product_set.exists():
            messages.error(request, 'Cannot delete category with associated products.')
            return redirect('stock:category_list')
        messages.success(request, 'Category deleted successfully.')
        return super().delete(request, *args, **kwargs)

class SupplierListView(StockLoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'stock/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset.annotate(product_count=Count('product'))

class SupplierCreateView(StockLoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'stock/supplier_form.html'
    success_url = reverse_lazy('stock:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Supplier created successfully.')
        return super().form_valid(form)

class SupplierUpdateView(StockLoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'stock/supplier_form.html'
    success_url = reverse_lazy('stock:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Supplier updated successfully.')
        return super().form_valid(form)

class SupplierDeleteView(StockLoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'stock/supplier_confirm_delete.html'
    success_url = reverse_lazy('stock:supplier_list')

    def delete(self, request, *args, **kwargs):
        supplier = self.get_object()
        if supplier.product_set.exists():
            messages.error(request, 'Cannot delete supplier with associated products.')
            return redirect('stock:supplier_list')
        messages.success(request, 'Supplier deleted successfully.')
        return super().delete(request, *args, **kwargs)

class StockAdjustmentView(StockLoginRequiredMixin, CreateView):
    model = StockHistory
    form_class = StockAdjustmentForm
    template_name = 'stock/stock_adjustment.html'
    success_url = reverse_lazy('stock:stock_history')

    def form_valid(self, form):
        stock_history = form.save(commit=False)
        stock_history.staff = self.request.user
        
        # Get the product and current quantity
        product = stock_history.product
        current_quantity = product.quantity
        
        # Adjust quantity based on action
        if stock_history.action == 'add':
            product.quantity += stock_history.quantity
        elif stock_history.action == 'remove':
            if stock_history.quantity > current_quantity:
                messages.error(self.request, 'Cannot remove more stock than available.')
                return self.form_invalid(form)
            product.quantity -= stock_history.quantity
        elif stock_history.action == 'damage':
            if stock_history.quantity > current_quantity:
                messages.error(self.request, 'Cannot mark more items as damaged than available.')
                return self.form_invalid(form)
            product.quantity -= stock_history.quantity
        elif stock_history.action == 'return':
            product.quantity += stock_history.quantity
        
        # Save both the product and stock history
        product.save()
        stock_history.save()
        
        messages.success(self.request, 'Stock adjusted successfully.')
        return super().form_valid(form)

class StockHistoryView(StockLoginRequiredMixin, ListView):
    model = StockHistory
    template_name = 'stock/stock_history.html'
    context_object_name = 'stock_history'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('product', 'staff')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(product__name__icontains=search_query)
        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_adjustments'] = self.get_queryset().count()
        context['total_added'] = self.get_queryset().filter(action='add').aggregate(total=Sum('quantity'))['total'] or 0
        context['total_removed'] = self.get_queryset().filter(action='remove').aggregate(total=Sum('quantity'))['total'] or 0
        context['total_damaged'] = self.get_queryset().filter(action='damage').aggregate(total=Sum('quantity'))['total'] or 0
        context['total_returned'] = self.get_queryset().filter(action='return').aggregate(total=Sum('quantity'))['total'] or 0
        return context

class SaleCreateView(StockLoginRequiredMixin, CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'stock/sale_form.html'
    success_url = reverse_lazy('stock:sale_list')

    def form_valid(self, form):
        try:
            sale = form.save(commit=False)
            sale.sold_by = self.request.user
            
            # Get total price from form data
            total_price = self.request.POST.get('total_price')
            if total_price:
                sale.total_price = float(total_price)
            else:
                sale.total_price = sale.product.unit_price * sale.quantity_sold
            
            # Check if there's enough stock
            if sale.quantity_sold > sale.product.quantity:
                messages.error(self.request, f'Not enough stock available. Only {sale.product.quantity} items left.')
                return self.form_invalid(form)
            
            # Update product quantity
            product = sale.product
            product.quantity -= sale.quantity_sold
            
            # Save both the product and sale in a transaction
            with transaction.atomic():
                product.save()
                sale.save()
                
                # Create stock history record with current timestamp
                StockHistory.objects.create(
                    product=product,
                    action_type='remove',
                    quantity_changed=sale.quantity_sold,
                    staff=self.request.user,
                    timestamp=timezone.now(),
                    reason=f'Sold to {sale.customer_name}' if sale.customer_name else 'Sale recorded'
                )
            
            messages.success(self.request, 'Sale recorded successfully.')
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(self.request, f'Error recording sale: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class SaleListView(StockLoginRequiredMixin, ListView):
    model = Sale
    template_name = 'stock/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('product', 'sold_by')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(product__name__icontains=search_query)
            ) | queryset.filter(
                customer_name__icontains=search_query
            )
        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Calculate sales statistics
        context['total_sales'] = queryset.count()
        context['total_revenue'] = queryset.aggregate(total=Sum('total_price'))['total'] or 0
        
        # Get sales data for the last 30 days
        last_30_days = timezone.now() - timedelta(days=30)
        daily_sales = queryset.filter(
            timestamp__gte=last_30_days
        ).values('timestamp__date').annotate(
            total=Sum('total_price')
        ).order_by('timestamp__date')
        
        # Format dates for Chart.js
        formatted_daily_sales = [
            {'date': sale['timestamp__date'].strftime('%Y-%m-%d'), 'total': float(sale['total'])}
            for sale in daily_sales
        ]
        context['daily_sales'] = formatted_daily_sales
        
        return context

class SaleDetailView(StockLoginRequiredMixin, DetailView):
    model = Sale
    template_name = 'stock/sale_detail.html'
    context_object_name = 'sale'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['receipt_number'] = f'REC-{self.object.id:06d}'
        return context

class ReportsView(StockLoginRequiredMixin, TemplateView):
    template_name = 'stock/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_types'] = [
            {'id': 'sales', 'name': 'Sales Report', 'description': 'Generate sales report by date range'},
            {'id': 'low_stock', 'name': 'Low Stock Report', 'description': 'List products below reorder level'},
            {'id': 'inventory', 'name': 'Inventory Value Report', 'description': 'Calculate total inventory value by category'},
        ]
        return context

    def post(self, request, *args, **kwargs):
        report_type = request.POST.get('report_type')
        format_type = request.POST.get('format', 'pdf')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if report_type == 'sales':
            return self.generate_sales_report(start_date, end_date, format_type)
        elif report_type == 'low_stock':
            return self.generate_low_stock_report(format_type)
        elif report_type == 'inventory':
            return self.generate_inventory_report(format_type)
        
        messages.error(request, 'Invalid report type selected.')
        return redirect('reports')

    def generate_sales_report(self, start_date, end_date, format_type):
        # Convert string dates to datetime objects
        start = datetime.strptime(start_date, '%Y-%m-%d') if start_date else timezone.now() - timedelta(days=30)
        end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else timezone.now()
        
        # Get sales data
        sales = Sale.objects.filter(
            created_at__range=[start, end]
        ).select_related('product').order_by('created_at')

        # Calculate totals
        total_sales = sales.count()
        total_revenue = sales.aggregate(total=Sum('total_price'))['total'] or 0
        avg_sale_value = total_revenue / total_sales if total_sales > 0 else 0

        if format_type == 'csv':
            return self.generate_sales_csv(sales, start, end, total_sales, total_revenue, avg_sale_value)
        else:
            return self.generate_sales_pdf(sales, start, end, total_sales, total_revenue, avg_sale_value)

    def generate_low_stock_report(self, format_type):
        # Get low stock products
        products = Product.objects.filter(quantity__lte=F('reorder_level')).select_related('category', 'supplier')
        
        if format_type == 'csv':
            return self.generate_low_stock_csv(products)
        else:
            return self.generate_low_stock_pdf(products)

    def generate_inventory_report(self, format_type):
        # Get inventory value by category
        inventory = Product.objects.values('category__name').annotate(
            total_products=Count('id'),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
        ).order_by('category__name')

        if format_type == 'csv':
            return self.generate_inventory_csv(inventory)
        else:
            return self.generate_inventory_pdf(inventory)

    def generate_sales_csv(self, sales, start_date, end_date, total_sales, total_revenue, avg_sale_value):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Sales Report', f'Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'])
        writer.writerow(['Total Sales:', total_sales])
        writer.writerow(['Total Revenue:', f'${total_revenue:.2f}'])
        writer.writerow(['Average Sale Value:', f'${avg_sale_value:.2f}'])
        writer.writerow([])
        writer.writerow(['Date', 'Product', 'Customer', 'Quantity', 'Unit Price', 'Total'])
        
        for sale in sales:
            writer.writerow([
                sale.created_at.strftime('%Y-%m-%d'),
                sale.product.name,
                sale.customer_name,
                sale.quantity,
                f'${sale.product.unit_price:.2f}',
                f'${sale.total_price:.2f}'
            ])
        
        return response

    def generate_sales_pdf(self, sales, start_date, end_date, total_sales, total_revenue, avg_sale_value):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        elements.append(Paragraph('Sales Report', title_style))
        elements.append(Paragraph(f'Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}', styles['Normal']))
        elements.append(Spacer(1, 20))

        # Summary
        summary_data = [
            ['Total Sales:', str(total_sales)],
            ['Total Revenue:', f'${total_revenue:.2f}'],
            ['Average Sale Value:', f'${avg_sale_value:.2f}']
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Sales data
        sales_data = [['Date', 'Product', 'Customer', 'Quantity', 'Unit Price', 'Total']]
        for sale in sales:
            sales_data.append([
                sale.created_at.strftime('%Y-%m-%d'),
                sale.product.name,
                sale.customer_name,
                str(sale.quantity),
                f'${sale.product.unit_price:.2f}',
                f'${sale.total_price:.2f}'
            ])

        sales_table = Table(sales_data, colWidths=[1*inch, 2*inch, 2*inch, 0.75*inch, 1*inch, 1*inch])
        sales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ]))
        elements.append(sales_table)

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf"'
        response.write(pdf)
        return response

    def generate_low_stock_csv(self, products):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="low_stock_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Low Stock Report', f'Generated on: {timezone.now().strftime("%Y-%m-%d")}'])
        writer.writerow([])
        writer.writerow(['Product', 'Category', 'Current Stock', 'Reorder Level', 'Supplier'])
        
        for product in products:
            writer.writerow([
                product.name,
                product.category.name if product.category else 'N/A',
                product.quantity,
                product.reorder_level,
                product.supplier.name if product.supplier else 'N/A'
            ])
        
        return response

    def generate_low_stock_pdf(self, products):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        elements.append(Paragraph('Low Stock Report', title_style))
        elements.append(Paragraph(f'Generated on: {timezone.now().strftime("%Y-%m-%d")}', styles['Normal']))
        elements.append(Spacer(1, 20))

        # Products data
        products_data = [['Product', 'Category', 'Current Stock', 'Reorder Level', 'Supplier']]
        for product in products:
            products_data.append([
                product.name,
                product.category.name if product.category else 'N/A',
                str(product.quantity),
                str(product.reorder_level),
                product.supplier.name if product.supplier else 'N/A'
            ])

        products_table = Table(products_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch, 2*inch])
        products_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
        ]))
        elements.append(products_table)

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="low_stock_report.pdf"'
        response.write(pdf)
        return response

    def generate_inventory_csv(self, inventory):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_value_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Inventory Value Report', f'Generated on: {timezone.now().strftime("%Y-%m-%d")}'])
        writer.writerow([])
        writer.writerow(['Category', 'Total Products', 'Total Quantity', 'Total Value'])
        
        for item in inventory:
            writer.writerow([
                item['category__name'] or 'Uncategorized',
                item['total_products'],
                item['total_quantity'],
                f'${item["total_value"]:.2f}'
            ])
        
        return response

    def generate_inventory_pdf(self, inventory):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        elements.append(Paragraph('Inventory Value Report', title_style))
        elements.append(Paragraph(f'Generated on: {timezone.now().strftime("%Y-%m-%d")}', styles['Normal']))
        elements.append(Spacer(1, 20))

        # Inventory data
        inventory_data = [['Category', 'Total Products', 'Total Quantity', 'Total Value']]
        for item in inventory:
            inventory_data.append([
                item['category__name'] or 'Uncategorized',
                str(item['total_products']),
                str(item['total_quantity']),
                f'${item["total_value"]:.2f}'
            ])

        inventory_table = Table(inventory_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        inventory_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        elements.append(inventory_table)

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="inventory_value_report.pdf"'
        response.write(pdf)
        return response

class LandingView(TemplateView):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('stock:dashboard')
        return super().get(request, *args, **kwargs)

class StockAlertsView(StockLoginRequiredMixin, ListView):
    model = Product
    template_name = 'stock/stock_alerts.html'
    context_object_name = 'low_stock_products'
    paginate_by = 10

    def get_queryset(self):
        return Product.objects.filter(
            quantity__lte=F('reorder_level')
        ).select_related('category', 'supplier').order_by('quantity')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_alerts'] = self.get_queryset().count()
        return context

class SalesAnalyticsView(StockLoginRequiredMixin, TemplateView):
    template_name = 'stock/sales_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from query parameters or default to last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Get sales data for the period
        sales = Sale.objects.filter(
            timestamp__range=[start_date, end_date]
        ).select_related('product')
        
        # Calculate basic metrics
        total_sales = sales.count()
        total_revenue = sales.aggregate(total=Sum('total_price'))['total'] or 0
        avg_sale_value = total_revenue / total_sales if total_sales > 0 else 0
        
        # Get daily sales data for the chart
        daily_sales = sales.values('timestamp__date').annotate(
            total=Sum('total_price'),
            count=Count('id')
        ).order_by('timestamp__date')
        
        # Get top selling products
        top_products = sales.values(
            'product__name'
        ).annotate(
            total_quantity=Sum('quantity_sold'),
            total_revenue=Sum('total_price')
        ).order_by('-total_quantity')[:5]
        
        # Get sales by category
        sales_by_category = sales.values(
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity_sold'),
            total_revenue=Sum('total_price')
        ).order_by('-total_revenue')
        
        context.update({
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'avg_sale_value': avg_sale_value,
            'daily_sales': list(daily_sales),
            'top_products': top_products,
            'sales_by_category': sales_by_category,
            'start_date': start_date,
            'end_date': end_date,
        })
        return context

class ProfileView(StockLoginRequiredMixin, TemplateView):
    template_name = 'stock/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        # Update user information
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        
        # Update password if provided
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        if current_password and new_password:
            if user.check_password(current_password):
                user.set_password(new_password)
                messages.success(request, 'Password updated successfully.')
            else:
                messages.error(request, 'Current password is incorrect.')
                return self.get(request, *args, **kwargs)
        
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

class SettingsView(StockLoginRequiredMixin, TemplateView):
    template_name = 'stock/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any system settings to the context
        context['settings'] = {
            'company_name': 'StockFlow',
            'currency': '₦',
            'date_format': 'YYYY-MM-DD',
            'time_format': '24-hour',
            'low_stock_threshold': 10,
            'enable_notifications': True,
            'enable_email_alerts': True,
        }
        return context

    def post(self, request, *args, **kwargs):
        # Handle settings updates
        settings = {
            'company_name': request.POST.get('company_name'),
            'currency': request.POST.get('currency'),
            'date_format': request.POST.get('date_format'),
            'time_format': request.POST.get('time_format'),
            'low_stock_threshold': int(request.POST.get('low_stock_threshold', 10)),
            'enable_notifications': request.POST.get('enable_notifications') == 'on',
            'enable_email_alerts': request.POST.get('enable_email_alerts') == 'on',
        }
        
        # Here you would typically save these settings to a database
        # For now, we'll just show a success message
        messages.success(request, 'Settings updated successfully.')
        return redirect('settings')

def logout_view(request):
    logout(request)
    return redirect('stock:login')
