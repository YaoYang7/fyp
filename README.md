# Multi-Tenant Blog Platform

A full-stack blog platform where users register into named groups (tenants) and collaboratively write, publish, and comment on blog posts. Published posts are also visible to the public without an account.

## Features

- **Multi-tenant groups** — users create or join a named group; posts and comments are scoped per group
- **Rich text editor** — Tiptap-powered editor with image and video embedding
- **Media uploads** — images and videos stored in Google Cloud Storage (500 MB per file, 2 GB per user)
- **Draft / publish workflow** — posts stay private as drafts until explicitly published
- **Comments** — tenant members can comment on any published post in their group
- **Public explore feed** — anyone can browse and read published posts without logging in
- **Dashboard** — personal stats (posts written, comments received, group activity)
- **Group user directory** — view all members of your group and their published post counts

## Tech Stack

### Frontend
- React 19.2.0, TypeScript 5.9.3, Vite 7.2.4
- Material-UI 7.3.7, TailwindCSS 4.1.18
- Redux Toolkit 2.11.2, React Router DOM 7.12.0
- Tiptap 3.19.0, Axios 1.13.2, DOMPurify 3.3.1

### Backend
- FastAPI 0.104.1, SQLAlchemy 2.0.23, Pydantic 2.5.0
- PostgreSQL (psycopg2-binary 2.9.9), Alembic 1.12.1
- bcrypt 5.0.0, python-jose, google-cloud-storage 2.16.0

## Cloud Run Deployment

The backend and frontend are deployed as separate Cloud Run services.

### Prerequisites

- Google Cloud project with Artifact Registry enabled
- Cloud SQL (PostgreSQL) instance or external PostgreSQL
- GCS bucket with a service account that has Storage Object Admin permissions

### 1. Build and push the backend

```bash
docker build -t REGION-docker.pkg.dev/PROJECT_ID/REPO/blog-backend ./blog-app/backend
docker push REGION-docker.pkg.dev/PROJECT_ID/REPO/blog-backend
```

Deploy to Cloud Run:

```bash
gcloud run deploy blog-backend \
  --image REGION-docker.pkg.dev/PROJECT_ID/REPO/blog-backend \
  --region REGION \
  --set-env-vars DATABASE_URL=postgresql://user:pass@host:5432/blogdb \
  --set-env-vars JWT_SECRET_KEY=your_long_random_secret \
  --set-env-vars CORS_ORIGINS=https://your-frontend.a.run.app \
  --set-env-vars GCS_BUCKET_NAME=your-gcs-bucket
```

Use `--service-account` with Workload Identity instead of `GOOGLE_APPLICATION_CREDENTIALS` where possible.

The backend listens on `$PORT` (injected by Cloud Run, defaults to 8080).

### 2. Build and push the frontend

Pass the backend URL as a build argument — it is baked into the JS bundle at build time:

```bash
docker build \
  --build-arg VITE_API_BASE_URL=https://your-backend.a.run.app \
  -t REGION-docker.pkg.dev/PROJECT_ID/REPO/blog-frontend \
  ./blog-app/frontend
docker push REGION-docker.pkg.dev/PROJECT_ID/REPO/blog-frontend
```

Deploy to Cloud Run:

```bash
gcloud run deploy blog-frontend \
  --image REGION-docker.pkg.dev/PROJECT_ID/REPO/blog-frontend \
  --region REGION \
  --allow-unauthenticated
```

### Environment variables

| Variable | Service | Description |
|---|---|---|
| `DATABASE_URL` | Backend | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Backend | JWT signing secret |
| `CORS_ORIGINS` | Backend | Comma-separated allowed origins (frontend URL) |
| `GCS_BUCKET_NAME` | Backend | GCS bucket for media uploads |
| `VITE_API_BASE_URL` | Frontend (build arg) | Backend Cloud Run URL |

