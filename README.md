# Virtual Business Card App

A modern, responsive web application for creating and sharing digital business cards via NFC tags and QR codes.

## 🌟 Features

### 📱 **Smart Contact Management**
- Multiple phone numbers with country codes and flags
- Searchable country dropdown with 195+ countries
- Primary phone designation
- WhatsApp integration
- Professional contact display

### 🎨 **UI Customization**
- Real-time color picker with live preview
- Custom gradient backgrounds
- Banner image support with text overlay
- Mobile-first responsive design

### 📊 **Analytics & Statistics**
- Visitor tracking with geolocation (IP-based)
- View counts and download statistics
- Country and city-level analytics
- Admin dashboard with detailed insights

### 💼 **Professional Features**
- Multiple profile types (Personal, Business, Freelance, etc.)
- Social media integration
- Custom links and portfolio URLs
- Automatic QR code generation
- vCard export for contact saving

### 🔧 **Admin Interface**
- Enhanced Django admin with color pickers
- Searchable country code selection
- Live color preview
- Bulk operations and management tools

## 🚀 Technology Stack

- **Backend:** Django 5.1.4 + Django REST Framework
- **Frontend:** Vanilla HTML/CSS/JavaScript (Mobile-optimized)
- **Database:** SQLite (development) / PostgreSQL (production ready)
- **Image Processing:** Pillow
- **QR Codes:** qrcode[pil]
- **Contact Export:** vobject
- **Geolocation:** IP-API integration

## 📋 Requirements

```
Django==5.1.4
djangorestframework==3.15.2
Pillow==11.0.0
qrcode[pil]==8.0
python-decouple==3.8
psycopg2-binary==2.9.10
vobject==0.9.6.1
requests==2.31.0
gunicorn==21.2.0
whitenoise==6.6.0
```

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/hosammo/vcard.git
cd vcard
```

### 2. Create virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment setup
Create a `.env` file in the project root:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

### 5. Database setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py populate_countries
python manage.py createsuperuser
```

### 6. Run the development server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` to access the admin interface.

## 📱 Usage

### Creating Business Cards
1. Access the Django admin interface
2. Create a new Business Card with your information
3. Add multiple phone numbers with country codes
4. Customize colors and upload images
5. Your unique URL will be auto-generated

### NFC Integration
1. Copy your business card URL
2. Write the URL to an NFC tag using any NFC writing app
3. Share your NFC tag - when scanned, it will display your business card

### Analytics
- View visitor statistics in the admin interface
- Track downloads and geographic distribution
- Monitor engagement over time

## 🌍 Deployment

Ready for deployment to shared hosting, VPS, or cloud platforms:

- Configure production database (PostgreSQL recommended)
- Set `DEBUG=False` in production
- Configure static file serving
- Set up SSL certificates
- Update `ALLOWED_HOSTS` with your domain

## 🎯 Use Cases

- **Professional Networking:** Replace traditional paper business cards
- **Events & Conferences:** Quick contact sharing via NFC
- **Real Estate:** Property listings with agent contact
- **Restaurants:** Menu and contact information
- **Freelancers:** Portfolio and contact sharing
- **Small Businesses:** Digital presence and contact management

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For support and questions, please open an issue on GitHub.

---

**Built with ❤️ for modern digital networking**