# ABE Portal - Paperless-ngx Frontend

Ein produktionsreifes, containerisiertes Web-Portal für die Verwaltung von ABE/Homologation PDFs mit Paperless-ngx Backend.

## Features

- **Authentifizierung**: Username + Password mit Argon2 Hashing und JWT Sessions
- **Rollen**: Admin und User mit verschiedenen Berechtigungen
- **Upload**: PDF-Upload direkt zu Paperless-ngx mit OCR-Integration
- **Suche**: Tolerante Suche nach E-Nummern und Modellnamen mit PostgreSQL Trigram
- **Download**: Gestreamte Downloads mit Audit-Logging
- **Admin UI**: Vollständige Benutzerverwaltung über die Web-Oberfläche
- **n8n API**: REST API Hook für automatisierte Suchen
- **Audit-Logging**: Vollständige Nachverfolgung aller Aktionen

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy, Alembic
- **Datenbank**: PostgreSQL 15+ mit pg_trgm und unaccent Extensions
- **Cache**: Redis für Rate Limiting
- **Container**: Docker Compose für einfache Deployment

## Schnellstart

### Voraussetzungen

- Docker und Docker Compose
- Synology NAS mit DSM 7.0+
- Paperless-ngx Installation (separat)

### Installation

1. **Repository klonen:**
```bash
git clone <repository-url>
cd ABE-Base
```

2. **Umgebungsvariablen konfigurieren:**
```bash
cp .env.example .env
# Bearbeiten Sie .env mit Ihren Werten
```

3. **Services starten:**
```bash
docker-compose up -d
```

4. **Initial Admin erstellen:**
Besuchen Sie `http://localhost:3000/setup` oder verwenden Sie die ENV-Variablen `ADMIN_USERNAME` und `ADMIN_PASSWORD`.

## Synology NAS Deployment

### Reverse Proxy Konfiguration

1. **DSM Control Panel → Application Portal → Reverse Proxy**
2. **Neue Regel erstellen:**
   - **Quell-Protokoll**: HTTPS
   - **Hostname**: Ihre Domain (z.B. `portal.example.com`)
   - **Port**: 443
   - **Ziel-Protokoll**: HTTP
   - **Hostname**: `localhost`
   - **Port**: 3000

3. **Header konfigurieren:**
   - `X-Forwarded-For`: `$remote_addr`
   - `X-Forwarded-Proto`: `$scheme`
   - `X-Forwarded-Host`: `$host`

4. **Upload-Größe erhöhen:**
   In der nginx-Konfiguration:
   ```nginx
   client_max_body_size 50M;
   ```

### Portainer Deployment

1. **Portainer Stack erstellen:**
```yaml
version: '3.8'
services:
  # Kopieren Sie den Inhalt von docker-compose.yml hier
```

2. **Umgebungsvariablen in Portainer setzen**
3. **Stack deployen**

## n8n Integration

### API Hook verwenden

```javascript
// HTTP Request Node in n8n
POST /api/hooks/search
Content-Type: application/json

{
  "query": "BMW X5",
  "eNumber": "e13*1234*5678*00",
  "limit": 10
}
```

**Antwort:**
```json
[
  {
    "docId": "12345",
    "title": "BMW X5 Homologation E13",
    "snippet": "...",
    "downloadUrl": "/api/doc/12345/download"
  }
]
```

## Konfiguration

### Umgebungsvariablen

Wichtige Konfigurationsoptionen in `.env`:

```bash
# Paperless-ngx Integration
PAPERLESS_BASE_URL=https://your-paperless.com
PAPERLESS_API_TOKEN=your-api-token

# Sicherheit
JWT_SECRET=your-secure-random-secret
RATE_LIMIT_LOGIN_PER_MIN=10

# Upload Limits
MAX_UPLOAD_MB=50

# Admin Bootstrap
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password
```

## Entwicklung

### Backend starten

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend starten

```bash
cd frontend
npm install
npm run dev
```

### Tests ausführen

```bash
cd backend
pytest

cd frontend
npm test
```

## API Dokumentation

Nach dem Start verfügbar unter:
- Backend API: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`

## Lizenz

MIT License
