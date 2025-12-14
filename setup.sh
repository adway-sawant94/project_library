#!/bin/bash
# setup.sh - Quick setup script for Engineering Projects SaaS

echo "🚀 Engineering Projects SaaS - Setup Script"
echo "==========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "📁 Creating project directories..."
mkdir -p media/projects/images
mkdir -p media/projects/files
mkdir -p static/css
mkdir -p static/js
mkdir -p staticfiles
mkdir -p templates/projects
mkdir -p templates/auth
mkdir -p templates/dashboard
mkdir -p templates/payments
mkdir -p templates/static

# Copy environment file
echo ""
echo "🔑 Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file. Please update it with your credentials."
else
    echo "✓ .env file already exists."
fi

# Run migrations
echo ""
echo "🗄️  Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Create superuser
echo ""
echo "👤 Create superuser account..."
echo "Please enter superuser credentials:"
python manage.py createsuperuser

# Collect static files
echo ""
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Final instructions
echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your credentials:"
echo "   - SECRET_KEY"
echo "   - RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET"
echo "   - Email settings"
echo ""
echo "2. Run the development server:"
echo "   python manage.py runserver"
echo ""
echo "3. Access the application:"
echo "   - Website: http://127.0.0.1:8000/"
echo "   - Admin: http://127.0.0.1:8000/admin/"
echo ""
echo "4. Add sample projects through admin panel"
echo ""
echo "Happy coding! 🎉"