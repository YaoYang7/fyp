from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

# Tenant Schemas
class TenantBase(BaseModel):
    name: str

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: int
    slug: str
    created_at: datetime

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    tenant_name: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str

class User(UserBase):
    id: int
    tenant_id: int
    tenant_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserInDB(User):
    password_hash: str

class UserLogin(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    message: str
    user: User
    token: str

# Blog Post Schemas
class PostStatus(str, Enum):
    published = "published"
    draft = "draft"

class BlogPostBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    status: PostStatus = PostStatus.draft

class BlogPostCreate(BlogPostBase):
    pass

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    status: Optional[PostStatus] = None

class BlogPost(BlogPostBase):
    id: int
    author_id: int
    author: str  # Username of the author
    views: int
    comments: int  # Count of comments
    date: str  # Formatted date for frontend
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Comment Schemas
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    post_id: int

class Comment(CommentBase):
    id: int
    author_id: int
    post_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Follower Schemas
class FollowerBase(BaseModel):
    following_id: int

class FollowerCreate(FollowerBase):
    pass

class Follower(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard Schemas
class DashboardStats(BaseModel):
    totalPosts: int
    totalViews: int
    totalComments: int
    totalFollowers: int
