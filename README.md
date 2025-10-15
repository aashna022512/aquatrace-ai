# AquaTrace AI - Marine Species Identification

A Flask-based web application for identifying marine species using AI and providing comprehensive species information.

## Features

### 🔐 User Authentication & Database
- User registration and login system
- SQLite database for storing user data and upload history
- Session management for secure authentication
- User profiles with upload statistics

### 🐠 Species Database
- Comprehensive marine species information
- Real fish images (replacing emojis)
- Conservation status and threats information
- Search and filter functionality
- New gradient background design

### ⭐ Premium Features
- Exclusive premium species database (requires login)
- Special marine creatures like Blue Whale and Great White Shark
- Enhanced UI with premium styling

### 📊 Dashboard & Analytics
- User-specific upload statistics
- Recent activity tracking
- Upload history with confidence scores
- Species diversity tracking

### 🖼️ Image Upload & AI
- AI-powered species identification
- Image upload functionality
- Confidence scoring
- Detailed species information display

## Installation & Setup

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aquatraceaimain
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**

   **For PowerShell (Windows):**
   ```powershell
   cd backend
   python app.py
   ```

   **For Command Prompt (Windows):**
   ```cmd
   cd backend
   python app.py
   ```

   **For Bash/Linux/Mac:**
   ```bash
   cd backend && python app.py
   ```

4. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:5000`

## Database Setup

The application automatically creates the SQLite database (`aquatrace.db`) on first run. The database includes:

- **Users table**: Stores user registration data
- **Uploads table**: Tracks image uploads and AI predictions
- **Species table**: Contains species information

## Usage

### Registration & Login
1. Click "Login" in the navigation
2. Click "Don't have an account?" to register
3. Fill in username, email, and password
4. Login with your credentials

### Species Identification
1. Upload an image of a marine species
2. The AI will identify the species and provide confidence score
3. View detailed information about the identified species
4. Your uploads are saved to your profile

### Species Database
- Browse the comprehensive species database
- Use search and filter options
- View conservation status and threats
- Access premium species (requires login)

### Dashboard
- View your upload statistics
- Track your species diversity
- See recent activity
- Monitor your contribution to marine science

## File Structure

```
aquatraceaimain/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── aquatrace.db          # SQLite database (auto-generated)
│   ├── species_info.json     # Species data
│   ├── templates/            # HTML templates
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   ├── profile.html
│   │   ├── species_database.html
│   │   ├── premium_species.html
│   │   └── result.html
│   └── static/              # CSS, JS, and assets
│       ├── style/
│       └── assets/
├── requirements.txt         # Python dependencies
└── README.md              # This file
```

## Recent Updates

### Bug Fixes
- ✅ Fixed login redirect issue (now redirects to dashboard)
- ✅ Fixed database initialization
- ✅ Fixed session management
- ✅ Fixed PowerShell command syntax

### New Features
- ✅ Added premium species database
- ✅ Replaced fish emojis with real images
- ✅ Updated species database background
- ✅ Enhanced user authentication
- ✅ Added comprehensive user profiles

### UI Improvements
- ✅ Better text visibility with darker blue overlay
- ✅ Premium gradient backgrounds
- ✅ Real fish images in species database
- ✅ Enhanced navigation with premium link

## Troubleshooting

### PowerShell Issues
If you encounter the error "The token '&&' is not a valid statement separator":
- Use separate commands: `cd backend` then `python app.py`
- Or use: `cd backend; python app.py`

### Database Issues
- Delete `aquatrace.db` file and restart the application
- The database will be recreated automatically

### Login Issues
- Clear your browser cookies and cache
- Ensure you're using the correct username/password
- Check that the database file exists

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please open an issue in the repository.
