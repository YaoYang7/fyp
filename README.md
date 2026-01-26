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

## Setup Instructions

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
