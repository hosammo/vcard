# deploy.sh - Run this script on your server after uploading files

#!/bin/bash
echo "🚀 Starting Virtual Business Card deployment to hosammo.com/vcard/..."

# Ensure we're using Python 3.13
echo "🐍 Using Python 3.13..."
python3.13 --version

# Install Python dependencies
echo "📦 Installing Python packages..."
pip3.13 install -r requirements.txt

# Database migrations
echo "🗄️ Running database migrations..."
python3.13 manage.py makemigrations --settings=vcard_project.settings_production
python3.13 manage.py migrate --settings=vcard_project.settings_production

# Create cache table
echo "💾 Creating cache table..."
python3.13 manage.py createcachetable --settings=vcard_project.settings_production

# Populate country codes
echo "🌍 Populating country codes..."
python3.13 manage.py populate_countries --settings=vcard_project.settings_production

# Collect static files
echo "📁 Collecting static files..."
python3.13 manage.py collectstatic --noinput --settings=vcard_project.settings_production

# Create superuser (interactive)
echo "👤 Creating admin user..."
echo "Please create your admin user:"
python3.13 manage.py createsuperuser --settings=vcard_project.settings_production

echo "✅ Deployment complete!"
echo "🌐 Your app should now be available at: https://hosammo.com/vcard/"
echo "🔑 Access admin at: https://hosammo.com/vcard/admin/"