# TikTok Video Publishing System

A web-based TikTok video publishing system that allows users to upload and publish videos to TikTok using the TikTok Content Posting API.

## Features

- **TikTok OAuth 2.0 Authentication**: Secure login with TikTok accounts
- **Video Upload**: Upload videos to TikTok inbox
- **Direct Publish**: Publish videos directly to TikTok
- **Privacy Settings**: Support multiple privacy levels
- **Upload History**: Track video upload and publish history
- **System Status**: Monitor authorization status and token expiration
- **Logout Functionality**: Secure logout with token cleanup

## Tech Stack

- **Backend**: Flask 2.3.x
- **Database**: SQLite (with SQLAlchemy)
- **Frontend**: HTML5, CSS3, JavaScript
- **API**: TikTok Content Posting API

## Project Structure

```
.
├── backend/                    # Backend API
│   ├── api.py                 # Flask main application
│   ├── config.py              # Configuration file
│   └── tiktok_callback.html   # OAuth callback page
├── frontend/                   # Frontend web interface
│   └── web_admin.html         # Main admin interface
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Vercel/Python configuration
├── .gitignore                 # Git ignore rules
└── README.md                  # Project documentation
```

## Installation

### Backend (Deployed on Railway)

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Frontend (Deployed on Vercel)

The frontend is a static HTML file that can be deployed directly on Vercel.

## Deployment Guide

### 🔹 Backend - Deploy to Railway

1. **Create Railway Project**
   - Go to [Railway.app](https://railway.app/)
   - Create new project from GitHub repo
   - Select your repository

2. **Set Environment Variables**
   | Variable | Value |
   |----------|-------|
   | `TIKTOK_CLIENT_KEY` | Your TikTok Client Key |
   | `TIKTOK_CLIENT_SECRET` | Your TikTok Client Secret |
   | `TIKTOK_REDIRECT_URI` | `https://your-railway-domain.up.railway.app/callback` |
   | `AUTH_SUCCESS_REDIRECT_URL` | `https://your-vercel-domain.vercel.app` |
   | `PORT` | `8000` |
   | `INTERNAL_API_KEY` | Your secret key |
   | `SECRET_KEY` | Flask secret key |

3. **Set Start Command**
   ```bash
   gunicorn backend.api:app
   ```

### 🔹 Frontend - Deploy to Vercel

1. **Create Vercel Project**
   - Go to [Vercel.com](https://vercel.com/)
   - Add new project from GitHub repo
   - Select your repository

2. **Configure Build Settings**
   - Framework: `Other`
   - Build Command: Leave empty
   - Output Directory: Leave empty

3. **Update API Base URL**
   - Edit `frontend/web_admin.html`
   - Update `API_BASE` to your Railway backend URL:
   ```javascript
   const API_BASE = 'https://your-railway-domain.up.railway.app/tiktok';
   ```

### 🔹 TikTok Developer Platform Configuration

1. Add callback URL: `https://your-railway-domain.up.railway.app/callback`
2. Ensure Content Posting API is enabled
3. Verify all required scopes are added

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Backend health check |
| `/callback` | GET | TikTok OAuth callback page |
| `/tiktok/auth/url` | GET | Get authorization URL |
| `/tiktok/auth/callback` | GET | OAuth callback handler |
| `/tiktok/upload` | POST | Upload video to inbox |
| `/tiktok/publish` | POST | Direct publish video |
| `/tiktok/status` | GET | Check authorization status |
| `/tiktok/logout` | POST | Logout and clear token |
| `/tiktok/history` | GET | Get upload history |
| `/tiktok/health` | GET | Health check |

## Security Notes

- CORS is configured to allow all origins for public access
- Token data is stored securely in SQLite database
- HTTPS is required for production deployment
- Users authenticate via TikTok OAuth 2.0

## License

This project is for internal use only.