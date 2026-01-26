from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas
from .security import get_password_hash, verify_password
from typing import Optional

def get_users(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(models.User)
    
    if search:
        query = query.filter(
            or_(
                models.User.username.ilike(f"%{search}%"),
                models.User.email.ilike(f"%{search}%"),
                models.User.full_name.ilike(f"%{search}%")
            )
        )
    
    return query.offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        update_data = user.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_password(db: Session, user_id: int, current_password: str, new_password: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user and verify_password(current_password, db_user.password_hash):
        db_user.password_hash = get_password_hash(new_password)
        db.commit()
        db.refresh(db_user)
        return db_user
    return None

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user