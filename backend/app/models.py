from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    first_name = Column(String(120), nullable=True)
    last_name = Column(String(120), nullable=True)
    birthday = Column(Date, nullable=True)
    position = Column(String(120), nullable=True)
    seniority = Column(String(32), nullable=True)
    avatar_200_path = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    avatar_images = relationship("AvatarImage", back_populates="user", cascade="all, delete-orphan")


class AvatarImage(Base):
    __tablename__ = "avatar_images"
    __table_args__ = (UniqueConstraint("user_id", "size", name="uq_avatar_images_user_size"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    size = Column(Integer, nullable=False)
    path = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="avatar_images")
