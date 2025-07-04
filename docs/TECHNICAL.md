# StockFlow Technical Documentation

## Architecture Overview

StockFlow follows a Model-View-Template (MVT) architecture pattern using Django, with a modern frontend built using Tailwind CSS and Alpine.js.

### Frontend Architecture

#### Components

1. **Card Component**
   - Location: `stock/templates/stock/partials/card.html`
   - Purpose: Provides consistent content containers with optional headers
   - Usage:
     ```html
     {% include 'stock/partials/card.html' with title="Title" subtitle="Subtitle" %}
         {% block card_content %}
             <!-- Content here -->
         {% endblock %}
     {% endinclude %}
     ```

2. **Form Component**
   - Location: `stock/templates/stock/partials/form.html`
   - Purpose: Standardized form layouts with built-in validation
   - Features:
     - Automatic field type detection
     - Error handling
     - Help text support
     - File upload handling
   - Usage:
     ```html
     {% include 'stock/partials/form.html' with form=form %}
         {% block form_actions %}
             <!-- Form buttons here -->
         {% endblock %}
     {% endinclude %}
     ```

3. **Tabs Component**
   - Location: `stock/templates/stock/partials/tabs.html`
   - Purpose: Interactive tab navigation using Alpine.js
   - Features:
     - Dynamic tab switching
     - Icon support
     - Responsive design
   - Usage:
     ```html
     {% include 'stock/partials/tabs.html' with tabs=tabs %}
         {% block tab_content %}
             <!-- Tab content here -->
         {% endblock %}
     {% endinclude %}
     ```

4. **Notifications System**
   - Location: `stock/templates/stock/partials/notifications.html`
   - Purpose: Toast notifications and confirmation modals
   - Features:
     - Toast notifications for actions
     - Confirmation modals for important actions
     - Low stock alerts
   - JavaScript Integration: `stock/static/js/notifications.js`

### JavaScript Integration

1. **Alpine.js Components**
   - Tab Navigation
   - Modal Dialogs
   - Form Validation
   - Dynamic Content Updates

2. **Chart.js Integration**
   - Sales Analytics
   - Stock Level Visualization
   - Performance Metrics

### CSS Architecture

1. **Tailwind CSS**
   - Custom color scheme
   - Responsive design patterns
   - Component-specific styles

2. **Custom Classes**
   - `.btn-primary`
   - `.btn-secondary`
   - `.text-text`
   - `.text-text/60`

## Database Models

1. **Product**
   - Basic information (name, SKU, description)
   - Stock management (quantity, reorder level)
   - Relationships (category, supplier)
   - Image handling

2. **Sale**
   - Transaction details
   - Customer information
   - Product relationships
   - Timestamps

3. **Supplier**
   - Contact information
   - Performance metrics
   - Product relationships

4. **Category**
   - Product categorization
   - Hierarchical structure

## API Endpoints

1. **Product Management**
   - `GET /products/` - List products
   - `POST /products/` - Create product
   - `GET /products/<id>/` - Product details
   - `PUT /products/<id>/` - Update product
   - `DELETE /products/<id>/` - Delete product

2. **Sales Management**
   - `GET /sales/` - List sales
   - `POST /sales/` - Create sale
   - `GET /sales/<id>/` - Sale details
   - `GET /sales/reports/` - Sales reports

3. **Supplier Management**
   - `GET /suppliers/` - List suppliers
   - `POST /suppliers/` - Create supplier
   - `GET /suppliers/<id>/` - Supplier details
   - `PUT /suppliers/<id>/` - Update supplier

## Security

1. **Authentication**
   - Django's built-in authentication system
   - Custom user model
   - Password reset functionality

2. **Authorization**
   - Role-based access control
   - Permission checks
   - CSRF protection

3. **Data Validation**
   - Form validation
   - Model validation
   - API request validation

## Performance Optimization

1. **Database**
   - Indexed fields
   - Optimized queries
   - Caching strategies

2. **Frontend**
   - Lazy loading
   - Asset optimization
   - Responsive images

## Testing

1. **Unit Tests**
   - Model tests
   - View tests
   - Form tests

2. **Integration Tests**
   - API tests
   - User flow tests
   - Component tests

## Deployment

1. **Requirements**
   - Python 3.8+
   - PostgreSQL (recommended)
   - Redis (for caching)

2. **Environment Variables**
   - `DEBUG`
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `ALLOWED_HOSTS`

3. **Static Files**
   - WhiteNoise configuration
   - CDN integration
   - Asset versioning 