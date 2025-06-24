# Chat-MBTI

## Development Environment

This project contains both the Flutter UI and the backend API for the Chat-MBTI application.

### Quick Start

1. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env file with your actual values
   ```

2. **Start all services with watch mode:**

   ```bash
   docker compose watch
   ```

3. **Access the applications:**
   - Flutter Web App: http://localhost:3000
   - API Backend: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database: localhost:5432

### Services

#### Flutter UI (`flutter` service)

- **Port:** 3000
- **Hot Reload:** Enabled via Docker Compose watch
- **Watches:** `lib/`, `web/`, `assets/` directories

#### API Backend (`api` service)

- **Port:** 8000
- **Hot Reload:** Enabled via Docker Compose watch
- **Watches:** `src/`, `config/` directories

#### PostgreSQL Database (`db` service)

- **Port:** 5432
- **Persistent data:** Stored in Docker volume `postgres_data`

### Development Commands

```bash
# Start all services in watch mode
docker compose watch

# Start specific service
docker compose up flutter
docker compose up api
docker compose up db

# View logs
docker compose logs -f flutter
docker compose logs -f api

# Stop all services
docker compose down

# Rebuild and restart
docker compose down && docker compose watch

# Remove all data (including database)
docker compose down -v
```

### File Structure

```
├── frontend/           # Flutter web application
│   ├── lib/              # Dart source code
│   ├── web/              # Web-specific files
│   └── Dockerfile        # Flutter container config
├── diagnosis-chat-api/     # Python FastAPI backend
│   ├── src/              # Python source code
│   ├── config/           # Configuration files
│   └── Dockerfile        # API container config
└── docker-compose.yaml   # Multi-service configuration
```

### Environment Variables

- `DB_CONNECTION_STRING`: PostgreSQL connection string
- `GEMINI_API_KEY`: Google Gemini AI API key
- `FLUTTER_WEB_USE_SKIA`: Enable Skia renderer for Flutter web
