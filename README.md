# TikTok Video Publishing System

A web-based TikTok video publishing system that allows users to upload and publish videos to TikTok using the TikTok Content Posting API.

## Features

- **TikTok OAuth 2.0 Authentication**: Secure login with TikTok accounts
- **Video Upload**: Upload videos to TikTok inbox
- **Direct Publish**: Publish videos directly to TikTok
- **Privacy Settings**: Support multiple privacy levels (Public, Followers Only, Mutual Follow Friends, Self Only, Private)
- **Upload History**: Track video upload and publish history
- **System Status**: Monitor authorization status and token expiration
- **Logout Functionality**: Secure logout with token cleanup

## Tech Stack

- **Backend**: Flask 2.3.x
- **Database**: SQLite (with SQLAlchemy)
- **Frontend**: HTML5, CSS3, JavaScript
- **API**: TikTok Content Posting API

## Requirements

- Python 3.8+
- TikTok Developer Account
- TikTok App with Content Posting API enabled

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tiktok-video-publishing
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

5. **Configure environment variables**
   
   Create a `.env` file with the following content:
   ```ini
   # TikTok API Configuration
   TIKTOK_CLIENT_KEY=your_client_key
   TIKTOK_CLIENT_SECRET=your_client_secret
   TIKTOK_REDIRECT_URI=https://your-domain.com/callback

   # Authorization success redirect URL
   AUTH_SUCCESS_REDIRECT_URL=http://localhost:8000

   # Server Configuration
   PORT=8000

   # TikTok API Endpoints
   TIKTOK_AUTH_URL=https://www.tiktok.com/v2/auth/authorize/
   TIKTOK_TOKEN_URL=https://open.tiktokapis.com/v2/oauth/token/
   TIKTOK_API_BASE_URL=https://open.tiktokapis.com/v2/

   # Internal API Key
   INTERNAL_API_KEY=your_internal_api_key
   ```

## Usage

### Run Development Server

```bash
python api.py
```

The application will be available at `http://localhost:8000`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page with web interface |
| `/callback` | GET | TikTok OAuth callback page |
| `/tiktok/auth/url` | GET | Get authorization URL |
| `/tiktok/auth/callback` | GET | OAuth callback handler |
| `/tiktok/upload` | POST | Upload video to inbox |
| `/tiktok/publish` | POST | Direct publish video |
| `/tiktok/status` | GET | Check authorization status |
| `/tiktok/logout` | POST | Logout and clear token |
| `/tiktok/history` | GET | Get upload history |
| `/tiktok/health` | GET | Health check |

## TikTok Developer Setup

1. Go to [TikTok Developer Portal](https://developers.tiktok.com/)
2. Create a new app
3. Enable Content Posting API
4. Add your redirect URI in the app settings
5. Get your Client Key and Client Secret

## Project Structure

```
.
├── api.py              # Main Flask application
├── config.py           # Configuration file
├── requirements.txt    # Python dependencies
├── web_admin.html      # Web admin interface
├── tiktok_callback.html # OAuth callback page
├── .env                # Environment variables (not in repo)
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

## Security Notes

- The application is designed for internal use only
- Access is restricted by IP whitelisting and API key authentication
- All API requests require an X-API-Key header
- Token data is stored securely in SQLite database
- HTTPS is required for production deployment

## License

This project is for internal use only.