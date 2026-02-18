import re
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc
from . import models, schemas
from .security import get_password_hash, verify_password
from typing import Optional, List


def _slugify(name: str) -> str:
    """Convert a tenant name to a URL-friendly slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug


# Tenant CRUD Operations
def create_tenant(db: Session, name: str) -> models.Tenant:
    slug = _slugify(name)
    db_tenant = models.Tenant(name=name, slug=slug)
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

def get_tenant_by_name(db: Session, name: str) -> Optional[models.Tenant]:
    slug = _slugify(name)
    return db.query(models.Tenant).filter(
        or_(models.Tenant.name == name, models.Tenant.slug == slug)
    ).first()


# User CRUD Operations
def get_users(db: Session, tenant_id: int, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(models.User).filter(models.User.tenant_id == tenant_id)

    if search:
        query = query.filter(
            or_(
                models.User.username.ilike(f"%{search}%"),
                models.User.email.ilike(f"%{search}%")
            )
        )

    return query.offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str, tenant_id: int):
    return db.query(models.User).filter(
        models.User.email == email,
        models.User.tenant_id == tenant_id
    ).first()

def get_user_by_username(db: Session, username: str, tenant_id: Optional[int] = None):
    query = db.query(models.User).filter(models.User.username == username)
    if tenant_id is not None:
        query = query.filter(models.User.tenant_id == tenant_id)
    return query.first()

def register_user(db: Session, user: schemas.UserCreate):
    # Find or create tenant
    tenant = get_tenant_by_name(db, user.tenant_name)
    if not tenant:
        tenant = create_tenant(db, user.tenant_name)

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        tenant_id=tenant.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def login_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# Blog Post CRUD Operations
def create_post(db: Session, post: schemas.BlogPostCreate, user_id: int, tenant_id: int):
    db_post = models.BlogPost(
        title=post.title,
        content=post.content,
        summary=post.summary,
        status=post.status,
        author_id=user_id,
        tenant_id=tenant_id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_post(db: Session, post_id: int, tenant_id: int):
    return db.query(models.BlogPost).filter(
        models.BlogPost.id == post_id,
        models.BlogPost.tenant_id == tenant_id
    ).first()

def get_tenant_posts(db: Session, tenant_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.BlogPost).filter(
        models.BlogPost.tenant_id == tenant_id,
        models.BlogPost.status == models.PostStatus.published
    ).order_by(desc(models.BlogPost.created_at)).offset(skip).limit(limit).all()

def get_user_posts(db: Session, user_id: int, tenant_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.BlogPost).filter(
        models.BlogPost.author_id == user_id,
        models.BlogPost.tenant_id == tenant_id
    ).order_by(desc(models.BlogPost.created_at)).offset(skip).limit(limit).all()

def get_recent_posts(db: Session, user_id: int, tenant_id: int, limit: int = 10):
    return db.query(models.BlogPost).filter(
        models.BlogPost.author_id == user_id,
        models.BlogPost.tenant_id == tenant_id
    ).order_by(desc(models.BlogPost.created_at)).limit(limit).all()

def update_post(db: Session, post_id: int, tenant_id: int, post_update: schemas.BlogPostUpdate):
    db_post = get_post(db, post_id, tenant_id)
    if not db_post:
        return None

    update_data = post_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)

    db.commit()
    db.refresh(db_post)
    return db_post

def delete_post(db: Session, post_id: int, tenant_id: int):
    db_post = get_post(db, post_id, tenant_id)
    if not db_post:
        return False

    db.delete(db_post)
    db.commit()
    return True

def search_posts(db: Session, query: str, user_id: int, tenant_id: int):
    return db.query(models.BlogPost).filter(
        models.BlogPost.author_id == user_id,
        models.BlogPost.tenant_id == tenant_id,
        or_(
            models.BlogPost.title.ilike(f"%{query}%"),
            models.BlogPost.content.ilike(f"%{query}%")
        )
    ).order_by(desc(models.BlogPost.created_at)).all()


# Comment CRUD Operations
def create_comment(db: Session, comment: schemas.CommentCreate, user_id: int, tenant_id: int):
    db_comment = models.Comment(
        content=comment.content,
        author_id=user_id,
        post_id=comment.post_id,
        tenant_id=tenant_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_post_comments(db: Session, post_id: int, tenant_id: int):
    return db.query(models.Comment).filter(
        models.Comment.post_id == post_id,
        models.Comment.tenant_id == tenant_id
    ).order_by(desc(models.Comment.created_at)).all()

def get_comment(db: Session, comment_id: int, tenant_id: int):
    return db.query(models.Comment).filter(
        models.Comment.id == comment_id,
        models.Comment.tenant_id == tenant_id
    ).first()

def delete_comment(db: Session, comment_id: int, tenant_id: int):
    db_comment = get_comment(db, comment_id, tenant_id)
    if not db_comment:
        return False

    db.delete(db_comment)
    db.commit()
    return True


# Dashboard Statistics
def get_dashboard_stats(db: Session, user_id: int, tenant_id: int):
    total_posts = db.query(func.count(models.BlogPost.id)).filter(
        models.BlogPost.author_id == user_id,
        models.BlogPost.tenant_id == tenant_id
    ).scalar()

    total_comments = db.query(func.count(models.Comment.id)).join(
        models.BlogPost
    ).filter(
        models.BlogPost.author_id == user_id,
        models.BlogPost.tenant_id == tenant_id
    ).scalar()

    return {
        "totalPosts": total_posts,
        "totalComments": total_comments,
    }


# Upload CRUD Operations
def create_upload(db: Session, filename: str, original_filename: str,
                  content_type: str, file_size: int, user_id: int, tenant_id: int):
    db_upload = models.Upload(
        filename=filename,
        original_filename=original_filename,
        content_type=content_type,
        file_size=file_size,
        user_id=user_id,
        tenant_id=tenant_id,
    )
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    return db_upload


def get_user_storage_used(db: Session, user_id: int) -> int:
    result = db.query(func.coalesce(func.sum(models.Upload.file_size), 0)).filter(
        models.Upload.user_id == user_id
    ).scalar()
    return result


def extract_upload_filenames(content: str, tenant_id: int) -> list:
    """Extract upload filenames from post HTML content."""
    pattern = rf'/uploads/{tenant_id}/([a-f0-9]{{32}}\.[a-zA-Z0-9]+)'
    return re.findall(pattern, content)
