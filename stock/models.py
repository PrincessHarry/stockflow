from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def needs_reorder(self):
        return self.quantity <= self.reorder_level

class StockHistory(models.Model):
    ACTION_TYPES = [
        ('add', 'Add Stock'),
        ('remove', 'Remove Stock'),
        ('damage', 'Damaged Stock'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    quantity_changed = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    staff = models.ForeignKey(User, on_delete=models.PROTECT)
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Stock Histories"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action_type} - {self.product.name} ({self.quantity_changed})"

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_sold = models.IntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    sold_by = models.ForeignKey(User, on_delete=models.PROTECT)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Sale of {self.product.name} ({self.quantity_sold})"

    def save(self, *args, **kwargs):
        # Update product quantity when sale is made
        if not self.pk:  # Only update stock if this is a new sale
            product = self.product
            if product.quantity < self.quantity_sold:
                raise ValueError(f'Not enough stock available. Only {product.quantity} units left.')
            product.quantity -= self.quantity_sold
            product.save()
        super().save(*args, **kwargs)
