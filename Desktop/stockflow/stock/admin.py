from django.contrib import admin
from .models import Category, Supplier, Product, StockHistory, Sale

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'email')
    list_filter = ('created_at',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'quantity', 'unit_price', 'reorder_level', 'supplier', 'needs_reorder')
    list_filter = ('category', 'supplier', 'created_at', 'updated_at')
    search_fields = ('name', 'sku')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'category', 'supplier', 'image')
        }),
        ('Stock Information', {
            'fields': ('quantity', 'unit_price', 'reorder_level')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'action_type', 'quantity_changed', 'timestamp', 'staff')
    list_filter = ('action_type', 'timestamp', 'staff')
    search_fields = ('product__name', 'reason')
    readonly_fields = ('timestamp',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_sold', 'total_price', 'sold_by', 'timestamp')
    list_filter = ('timestamp', 'sold_by')
    search_fields = ('product__name',)
    readonly_fields = ('timestamp',)
