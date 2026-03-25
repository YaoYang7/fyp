from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, UniqueConstraint, Boolean, Float, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base
import enum


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    posts = relationship("BlogPost", back_populates="tenant", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="tenant", cascade="all, delete-orphan")
    uploads = relationship("Upload", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", "tenant_id", name="uq_user_username_tenant"),
        UniqueConstraint("email", "tenant_id", name="uq_user_email_tenant"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, index=True)
    email = Column(String(100), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    posts = relationship("BlogPost", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    uploads = relationship("Upload", back_populates="user", cascade="all, delete-orphan")



class PostStatus(str, enum.Enum):
    published = "published"
    draft = "draft"


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    status = Column(Enum(PostStatus, native_enum=False), default=PostStatus.draft, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="posts")
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("blog_posts.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="comments")
    author = relationship("User", back_populates="comments")
    post = relationship("BlogPost", back_populates="comments")


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="uploads")
    tenant = relationship("Tenant", back_populates="uploads")


class TenantResourceProfile(Base):
    __tablename__ = "tenant_resource_profiles"

    tenant_id    = Column(Integer, ForeignKey("tenants.id"), primary_key=True)
    ram_class    = Column(String(10), nullable=False, default="small")
    # "small"=64MB, "medium"=128MB, "large"=256MB
    footprint_mb = Column(Integer, nullable=False, default=64)
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantPlacement(Base):
    __tablename__ = "tenant_placements"

    tenant_id    = Column(Integer, ForeignKey("tenants.id"), primary_key=True)
    backend_name = Column(String(100), nullable=False)   # e.g. "vm1"
    backend_host = Column(String(200), nullable=False)   # e.g. "vm1:8000"
    assigned_at  = Column(DateTime(timezone=True), server_default=func.now())
    is_active    = Column(Boolean, nullable=False, default=True)


class TenantMetrics(Base):
    __tablename__ = "tenant_metrics"

    tenant_id     = Column(Integer, ForeignKey("tenants.id"), primary_key=True)
    avg_cpu_ms    = Column(Float, nullable=False, default=0.0)    # EMA of request processing time
    avg_bytes_out = Column(BigInteger, nullable=False, default=0)  # EMA of response bytes per request
    request_count = Column(BigInteger, nullable=False, default=0)  # cumulative requests tracked
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
