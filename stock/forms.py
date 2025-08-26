from django import forms
from .models import Product, Category, Supplier, StockHistory, Sale

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'quantity', 'unit_price', 
                 'supplier', 'reorder_level', 'image', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'sku': forms.TextInput(attrs={'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
            self.fields['supplier'].queryset = Supplier.objects.filter(user=user)
        self._current_user = user

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        user = getattr(self, '_current_user', None)
        if not sku:
            return sku
        qs = Product.objects.filter(sku=sku)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        # If per-user uniqueness is intended, also filter by user
        if user is not None:
            qs = qs.filter(user=user)
        if qs.exists():
            raise forms.ValidationError('A product with this SKU already exists.')
        return sku

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockHistory
        fields = ['product', 'action_type', 'quantity_changed', 'reason']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity_changed': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
            'reason': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['product'].queryset = Product.objects.filter(user=user).order_by('name')
        else:
            self.fields['product'].queryset = Product.objects.all().order_by('name')
        self.fields['action_type'].choices = [
            ('add', 'Add Stock'),
            ('remove', 'Remove Stock'),
            ('damage', 'Mark as Damaged'),
        ]

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product', 'quantity_sold', 'total_price', 'customer_name', 'customer_email', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity_sold': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['product'].queryset = Product.objects.filter(user=user, quantity__gt=0).order_by('name')
        else:
            self.fields['product'].queryset = Product.objects.filter(quantity__gt=0).order_by('name')
        self.fields['customer_name'].required = False
        self.fields['customer_email'].required = False
        self.fields['notes'].required = False

    def clean_quantity_sold(self):
        quantity = self.cleaned_data['quantity_sold']
        product = self.cleaned_data['product']
        if quantity > product.quantity:
            raise forms.ValidationError(f'Only {product.quantity} units available in stock.')
        return quantity

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'request'):
            instance.sold_by = self.request.user
        if commit:
            instance.save()
        return instance 