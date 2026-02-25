# Multi Tenant Blog Platform

A full-stack blog platform built with React, TypeScript, FastAPI, and PostgreSQL.

## Requirements

### Frontend
- Node.js (v18 or higher recommended)
- npm (comes with Node.js)

### Backend
- Python 3.10 or higher
- PostgreSQL 12 or higher

### Tools
- PowerShell (for Windows development script)
- Google Chrome (for automated browser launch)

## Tech Stack

### Frontend
- React 19.2.0
- TypeScript 5.9.3
- Vite 7.2.4
- Material-UI (MUI) 7.3.7
- TailwindCSS 4.1.18
- React Router DOM 7.12.0
- Axios 1.13.2

### Backend
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- PostgreSQL with psycopg2-binary
- Alembic (database migrations)
- Pydantic 2.5.0
- Passlib (password hashing)

## Docker Deployment

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Create a `.env` file

Create a `.env` file in the project root (next to `docker-compose.yml`):

```env
# PostgreSQL password
POSTGRES_PASSWORD=your_secure_password

# JWT signing secret — generate with:
# python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your_long_random_secret

# Allowed CORS origins (comma-separated)
# Use your server IP or domain in production
CORS_ORIGINS=http://localhost
```

### 2. Build and start all services

```bash
docker compose up --build
```

This starts three services:

- `postgres` — PostgreSQL 15 database (internal only)
- `backend` — FastAPI app (Uvicorn, 2 workers) (internal only)
- `frontend` — React SPA served by Nginx (port **80**)

The app is available at **http://localhost** once all health checks pass (~30 s on first boot).

### 3. Stop services

```bash
# Stop containers, keep volumes (data is preserved)
docker compose down

# Stop containers AND delete all data (database + uploads)
docker compose down -v
```

### Persistent volumes

- `postgres_data` — PostgreSQL database files
- `uploads_data` — User-uploaded files

### How Nginx routes requests

Nginx (port 80) serves the React SPA and proxies API routes to the backend internally — no backend port is exposed to the host.

- `/api/` → `http://backend:8000/api/`
- `/user_api/` → `http://backend:8000/user_api/`
- `/uploads/` → `http://backend:8000/uploads/`
- all other paths → React SPA (`index.html`)

---

## Local Development Setup

### 1. Backend Setup
Install dependencies:
```bash
pip install -r requirements.txt
```

Configure environment variables:
- Create a `.env` file in the backend directory
- Add your database connection string and other required variables

Set up the database:
```bash
# Create PostgreSQL database
# Then run migrations
alembic upgrade head
```

### 2. Frontend Setup

Navigate to the frontend directory:
```bash
cd blog-app/frontend
```

Install dependencies:
```bash
npm install
```

### 3. Running the Application

#### Quick Start (Windows)
Run both frontend and backend with one command:
```powershell
.\runDev.ps1
```
This script will:
- Start the FastAPI backend on `http://localhost:8000`
- Start the Vite dev server on `http://localhost:5173`
- Automatically open the application in Google Chrome
