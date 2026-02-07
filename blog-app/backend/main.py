from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from app import models, schemas, crud
from app.db import engine, get_db
from app.auth import get_current_user
from app.security import create_access_token

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blog Application API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (development only!)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Blog Application API is running"}

# User Authentication Endpoints
@app.post("/user_api/register", response_model=schemas.User, status_code=201)
def register_user_endpoint(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account and create/join a tenant
    """
    tenant = crud.get_tenant_by_name(db, user.tenant_name)

    # Enforce create vs join mode
    if user.mode == "create":
        if tenant:
            raise HTTPException(status_code=400, detail="Group name already exists. Use 'Join' to join an existing group.")
    elif user.mode == "join":
        if not tenant:
            raise HTTPException(status_code=400, detail="Group not found. Check the name or use 'Create' to make a new group.")
    else:
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'create' or 'join'.")

    # Check uniqueness within the tenant (only relevant when joining)
    if tenant:
        db_user = crud.get_user_by_username(db, username=user.username, tenant_id=tenant.id)
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered in this group")

        db_user = crud.get_user_by_email(db, email=user.email, tenant_id=tenant.id)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered in this group")

    # Create the new user (and tenant if needed)
    return crud.register_user(db=db, user=user)

@app.post("/user_api/login", response_model=schemas.LoginResponse)
def login_user_endpoint(user_login: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and log them in
    """
    user = crud.login_user(db, username=user_login.username, password=user_login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Create JWT token with tenant_id
    access_token = create_access_token(data={"sub": str(user.id), "tenant_id": user.tenant_id})

    # Query users table to get tenant_id, then query tenants table for the name
    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    tenant = db.query(models.Tenant).filter(models.Tenant.id == db_user.tenant_id).first()

    user_data = {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "tenant_id": db_user.tenant_id,
        "tenant_name": tenant.name if tenant else None,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
    }

    return {
        "message": "Login successful",
        "user": user_data,
        "token": access_token,
    }

# Helper function to format blog post for frontend
def format_blog_post(post: models.BlogPost, db: Session) -> dict:
    """
    Format a BlogPost model to match the frontend BlogPost interface
    """
    comments_count = len(post.comments) if post.comments else 0

    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "summary": post.summary,
        "author": post.author.username,
        "author_id": post.author_id,
        "date": post.created_at.strftime("%Y-%m-%d"),
        "views": post.views,
        "comments": comments_count,
        "status": post.status.value,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat() if post.updated_at else None
    }

# Dashboard Endpoints
@app.get("/api/dashboard/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics for the current user
    """
    stats = crud.get_dashboard_stats(db, user_id=current_user.id, tenant_id=current_user.tenant_id)
    return stats

# Blog Post Endpoints
@app.get("/api/posts/feed")
def get_feed_posts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all published posts in the current user's tenant (feed)
    """
    posts = crud.get_tenant_posts(db, tenant_id=current_user.tenant_id, skip=skip, limit=limit)
    return [format_blog_post(post, db) for post in posts]

@app.get("/api/posts/recent")
def get_recent_posts(
    limit: int = Query(default=10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent posts for the current user
    """
    posts = crud.get_recent_posts(db, user_id=current_user.id, tenant_id=current_user.tenant_id, limit=limit)
    return [format_blog_post(post, db) for post in posts]

@app.get("/api/posts/user")
def get_user_posts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all posts for the current user
    """
    posts = crud.get_user_posts(db, user_id=current_user.id, tenant_id=current_user.tenant_id, skip=skip, limit=limit)
    return [format_blog_post(post, db) for post in posts]

@app.get("/api/posts/{post_id}")
def get_post(
    post_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific post by ID
    """
    post = crud.get_post(db, post_id=post_id, tenant_id=current_user.tenant_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if the current user owns this post
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this post")

    # Increment view count
    crud.increment_post_views(db, post_id=post_id, tenant_id=current_user.tenant_id)

    return format_blog_post(post, db)

@app.post("/api/posts", status_code=201)
def create_post(
    post: schemas.BlogPostCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new blog post
    """
    new_post = crud.create_post(db, post=post, user_id=current_user.id, tenant_id=current_user.tenant_id)
    return format_blog_post(new_post, db)

@app.put("/api/posts/{post_id}")
def update_post(
    post_id: int,
    post_update: schemas.BlogPostUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing blog post
    """
    existing_post = crud.get_post(db, post_id=post_id, tenant_id=current_user.tenant_id)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if the current user owns this post
    if existing_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")

    updated_post = crud.update_post(db, post_id=post_id, tenant_id=current_user.tenant_id, post_update=post_update)
    return format_blog_post(updated_post, db)

@app.delete("/api/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a blog post
    """
    existing_post = crud.get_post(db, post_id=post_id, tenant_id=current_user.tenant_id)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if the current user owns this post
    if existing_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    crud.delete_post(db, post_id=post_id, tenant_id=current_user.tenant_id)
    return None

@app.get("/api/posts/search")
def search_posts(
    q: str = Query(..., min_length=1),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search posts by title or content
    """
    posts = crud.search_posts(db, query=q, user_id=current_user.id, tenant_id=current_user.tenant_id)
    return [format_blog_post(post, db) for post in posts]

# Comment Endpoints
@app.get("/api/posts/{post_id}/comments")
def get_post_comments(
    post_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all comments for a specific post
    """
    post = crud.get_post(db, post_id=post_id, tenant_id=current_user.tenant_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = crud.get_post_comments(db, post_id=post_id, tenant_id=current_user.tenant_id)
    return comments

@app.post("/api/posts/{post_id}/comments", status_code=201)
def create_comment(
    post_id: int,
    comment: schemas.CommentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new comment on a post
    """
    post = crud.get_post(db, post_id=post_id, tenant_id=current_user.tenant_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = crud.create_comment(db, comment=comment, user_id=current_user.id, tenant_id=current_user.tenant_id)
    return new_comment
