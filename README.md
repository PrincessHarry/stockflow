# StockFlow - Inventory Management System

StockFlow is a modern, user-friendly inventory management system built with Django and Tailwind CSS. It helps businesses track their inventory, manage suppliers, and monitor sales efficiently.

## Features

- 📊 **Dashboard**: Real-time overview of inventory status
- 📦 **Product Management**: Add, edit, and track products with images
- 📈 **Stock Control**: Monitor stock levels and set reorder points
- 🔄 **Stock History**: Track all stock movements and adjustments
- 💰 **Sales Management**: Record and track sales transactions
- 👥 **Supplier Management**: Manage supplier information and contacts
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices
- 🔒 **User Authentication**: Secure login and password reset functionality

## Tech Stack

- **Backend**: Django 5.1
- **Frontend**: Tailwind CSS
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Django Authentication System
- **Static Files**: WhiteNoise
- **Forms**: Crispy Forms with Tailwind

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/stockflow.git
   cd stockflow
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv stockenv
   # On Windows
   stockenv\Scripts\activate
   # On macOS/Linux
   source stockenv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

7. Visit `http://127.0.0.1:8000` in your browser

## Project Structure

```
stockflow/
├── stock/                  # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── forms.py           # Form definitions
│   ├── urls.py            # URL routing
│   └── admin.py           # Admin interface
├── templates/             # HTML templates
├── static/               # Static files (CSS, JS, images)
├── media/                # User-uploaded files
├── stockflow/            # Project settings
└── manage.py             # Django management script
```

## Usage

1. **Login**: Access the system using your credentials
2. **Dashboard**: View key metrics and alerts
3. **Products**: Manage your product catalog
4. **Stock**: Monitor and adjust inventory levels
5. **Sales**: Record and track sales transactions
6. **Suppliers**: Manage supplier information

## Deployment

### Deploying to Render

1. Push your code to a Git repository (GitHub, GitLab, etc.)

2. Create a new Web Service on Render:
   - Connect your repository
   - Set the following:
     - Build Command: `./build.sh`
     - Start Command: `gunicorn stockflow.wsgi:application`
     - Environment Variables:
       - `SECRET_KEY`: Your Django secret key
       - `RENDER_EXTERNAL_HOSTNAME`: Will be set automatically

3. Important Notes:
   - The free tier of Render has some limitations:
     - Spins down after 15 minutes of inactivity
     - Limited storage (SQLite database)
     - Limited bandwidth
   - For production use, consider:
     - Upgrading to a paid plan
     - Using PostgreSQL instead of SQLite
     - Setting up proper backup solutions

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- Django Documentation
- Tailwind CSS
- Crispy Forms
- WhiteNoise 