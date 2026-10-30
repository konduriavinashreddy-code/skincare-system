from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    profile: Mapped["UserProfile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    analyses: Mapped[list["SkinAnalysis"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_products: Mapped[list["SavedProduct"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    age_range: Mapped[str | None] = mapped_column(String(30), nullable=True)
    skin_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    sensitivity: Mapped[str] = mapped_column(String(30), default="somewhat")
    allergies: Mapped[str] = mapped_column(Text, default="")
    budget: Mapped[str] = mapped_column(String(30), default="moderate")
    preferences: Mapped[list] = mapped_column(JSON, default=list)
    user: Mapped[User] = relationship(back_populates="profile")

class SkinAnalysis(Base):
    __tablename__ = "skin_analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    skin_type_estimate: Mapped[str] = mapped_column(String(30))
    confidence: Mapped[float] = mapped_column(Float)
    observations: Mapped[dict] = mapped_column(JSON)
    quality: Mapped[dict] = mapped_column(JSON)
    model_mode: Mapped[str] = mapped_column(String(20), default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    user: Mapped[User] = relationship(back_populates="analyses")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    brand: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text)
    skin_types: Mapped[list] = mapped_column(JSON, default=list)
    concerns: Mapped[list] = mapped_column(JSON, default=list)
    ingredients: Mapped[list] = mapped_column(JSON, default=list)
    suitable_for_sensitive_skin: Mapped[bool] = mapped_column(Boolean, default=False)
    fragrance_free: Mapped[bool] = mapped_column(Boolean, default=False)
    vegan: Mapped[bool] = mapped_column(Boolean, default=False)
    cruelty_free: Mapped[bool] = mapped_column(Boolean, default=False)
    price: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    amazon_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    flipkart_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    availability: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

class SavedProduct(Base):
    __tablename__ = "saved_products"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    user: Mapped[User] = relationship(back_populates="saved_products")