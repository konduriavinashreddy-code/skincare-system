import os
import secrets
from pathlib import Path

import jwt
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Product, SavedProduct, SkinAnalysis, User, UserProfile
from .security import JWT_ALGORITHM, JWT_SECRET, create_token, hash_password, verify_password
from .seed import seed_products
from .services.analysis import analyze_image
from .services.quality import inspect_image, preprocess
from .services.recommendations import rank_product, marketplace_links

# Don't create tables at import time for serverless
# Base.metadata.create_all(bind=engine)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads")).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024
DISCLAIMER = "DermaCare AI provides image-based skin-care observations and general product recommendations. It is not a medical diagnostic tool and should not replace professional medical advice."
app = FastAPI(title="DermaCare AI API", version="1.0.0", description=DISCLAIMER)
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def ok(data, message=""):
    return {"success": True, "data": data, "message": message}

def profile_json(profile):
    return {key: getattr(profile, key) for key in ("age_range", "skin_type", "sensitivity", "allergies", "budget", "preferences")}

def product_json(product, user=None):
    saved = bool(user and any(item.product_id == product.id for item in user.saved_products))
    return {"id": product.id, "name": product.name, "brand": product.brand, "category": product.category,
            "description": product.description, "skin_types": product.skin_types, "concerns": product.concerns,
            "ingredients": product.ingredients, "suitable_for_sensitive_skin": product.suitable_for_sensitive_skin,
            "fragrance_free": product.fragrance_free, "vegan": product.vegan, "cruelty_free": product.cruelty_free,
            "price": product.price, "currency": product.currency, "rating": product.rating,
            "image_url": product.image_url, "is_demo": product.is_demo, "saved": saved, **marketplace_links(product)}

def current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)):
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = db.get(User, int(claims["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        user = None
    if user is None:
        raise HTTPException(401, detail={"code": "UNAUTHORIZED", "message": "Please sign in again."})
    return user

@app.on_event("startup")
def startup():
    # Create tables at startup for serverless
    Base.metadata.create_all(bind=engine)
    session = next(get_db())
    try:
        seed_products(session)
    finally:
        session.close()

@app.get("/api/health")
def health():
    return ok({"status": "ok", "ai_mode": os.getenv("AI_MODE", "mock")})

@app.post("/api/auth/register")
def register(payload: dict, db: Session = Depends(get_db)):
    name, email, password = str(payload.get("full_name", "")).strip(), str(payload.get("email", "")).strip().lower(), str(payload.get("password", ""))
    if len(name) < 2 or "@" not in email or len(password) < 10:
        raise HTTPException(422, detail={"code": "INVALID_REGISTRATION", "message": "Enter a name, valid email, and password with at least 10 characters."})
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, detail={"code": "EMAIL_EXISTS", "message": "An account with this email already exists."})
    user = User(full_name=name[:120], email=email, password_hash=hash_password(password))
    user.profile = UserProfile()
    db.add(user); db.commit(); db.refresh(user)
    return ok({"access_token": create_token(user.id), "user": {"id": user.id, "full_name": user.full_name, "email": user.email}}, "Account created")

@app.post("/api/auth/login")
def login(payload: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=str(payload.get("email", "")).strip().lower()).first()
    if not user or not verify_password(str(payload.get("password", "")), user.password_hash):
        raise HTTPException(401, detail={"code": "INVALID_CREDENTIALS", "message": "Email or password was not recognized."})
    return ok({"access_token": create_token(user.id), "user": {"id": user.id, "full_name": user.full_name, "email": user.email}}, "Signed in")

@app.post("/api/auth/logout")
def logout(user=Depends(current_user)):
    return ok({}, "Remove the access token from this browser to sign out")

@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return ok({"id": user.id, "full_name": user.full_name, "email": user.email})

@app.get("/api/profile")
def get_profile(user=Depends(current_user)):
    return ok(profile_json(user.profile))

@app.put("/api/profile")
def update_profile(payload: dict, db: Session = Depends(get_db), user=Depends(current_user)):
    for key in ("age_range", "skin_type", "sensitivity", "allergies", "budget", "preferences"):
        if key in payload:
            value = payload[key]
            if key == "allergies": value = str(value)[:500]
            if key == "preferences" and not isinstance(value, list): value = []
            setattr(user.profile, key, value)
    db.commit()
    return ok(profile_json(user.profile), "Profile updated")

async def image_bytes(file: UploadFile):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, detail={"code": "UNSUPPORTED_IMAGE", "message": "Upload a JPG, PNG, or WEBP image."})
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content: raise HTTPException(400, detail={"code": "EMPTY_IMAGE", "message": "Choose a non-empty image."})
    if len(content) > MAX_UPLOAD_BYTES: raise HTTPException(413, detail={"code": "IMAGE_TOO_LARGE", "message": "Image exceeds the upload limit."})
    return content

@app.post("/api/skin/quality-check")
async def quality_check(file: UploadFile = File(...), user=Depends(current_user)):
    try: quality, _ = inspect_image(await image_bytes(file))
    except ValueError as exc: raise HTTPException(422, detail={"code": "INVALID_IMAGE", "message": str(exc)})
    return ok(quality)

@app.post("/api/skin/upload")
async def upload(file: UploadFile = File(...), user=Depends(current_user)):
    content = await image_bytes(file)
    try: quality, _ = inspect_image(content)
    except ValueError as exc: raise HTTPException(422, detail={"code": "INVALID_IMAGE", "message": str(exc)})
    if not quality["valid"]: raise HTTPException(422, detail={"code": "IMAGE_QUALITY_LOW", "message": "Image quality is insufficient.", "warnings": quality["warnings"]})
    file_id = secrets.token_urlsafe(24)
    (UPLOAD_DIR / f"{user.id}_{file_id}.image").write_bytes(content)
    return ok({"upload_id": file_id, "quality": quality}, "Image stored privately")

@app.post("/api/skin/analyze")
@app.post("/api/skin/camera")
async def analyze(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(current_user)):
    content = await image_bytes(file)
    try: quality, image = inspect_image(content)
    except ValueError as exc: raise HTTPException(422, detail={"code": "INVALID_IMAGE", "message": str(exc)})
    if not quality["valid"]: raise HTTPException(422, detail={"code": "IMAGE_QUALITY_LOW", "message": "Image quality is insufficient.", "warnings": quality["warnings"]})
    preprocess(image)
    try: result = analyze_image(content)
    except RuntimeError as exc: raise HTTPException(503, detail={"code": "AI_UNAVAILABLE", "message": str(exc)})
    record = SkinAnalysis(user_id=user.id, skin_type_estimate=result["skin_type_estimate"], confidence=result["confidence"], observations=result["observations"], quality=quality, model_mode=result["model_mode"])
    db.add(record); db.commit(); db.refresh(record)
    return ok({"id": record.id, "skin_type_estimate": record.skin_type_estimate, "confidence": record.confidence,
               "observations": record.observations, "quality": quality, "model_mode": record.model_mode,
               "mock_notice": result["disclaimer"], "disclaimer": DISCLAIMER, "created_at": record.created_at.isoformat()}, "Analysis completed")

def analysis_json(item):
    return {"id": item.id, "skin_type_estimate": item.skin_type_estimate, "confidence": item.confidence,
            "observations": item.observations, "quality": item.quality, "model_mode": item.model_mode,
            "created_at": item.created_at.isoformat(), "disclaimer": DISCLAIMER}

@app.get("/api/skin/history")
def history(db: Session = Depends(get_db), user=Depends(current_user)):
    items = db.query(SkinAnalysis).filter_by(user_id=user.id).order_by(SkinAnalysis.created_at.desc()).all()
    return ok([analysis_json(item) for item in items])

@app.get("/api/skin/analysis/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    item = db.query(SkinAnalysis).filter_by(id=analysis_id, user_id=user.id).first()
    if not item: raise HTTPException(404, detail={"code": "ANALYSIS_NOT_FOUND", "message": "Analysis not found."})
    return ok(analysis_json(item))

@app.delete("/api/skin/analysis/{analysis_id}")
def delete_analysis(analysis_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    item = db.query(SkinAnalysis).filter_by(id=analysis_id, user_id=user.id).first()
    if not item: raise HTTPException(404, detail={"code": "ANALYSIS_NOT_FOUND", "message": "Analysis not found."})
    db.delete(item); db.commit()
    return ok({}, "Analysis deleted")

@app.get("/api/products")
def products(search: str = "", category: str = "", vegan: bool = False, fragrance_free: bool = False, db: Session = Depends(get_db), user=Depends(current_user)):
    query = db.query(Product).filter(Product.availability.is_(True))
    if search: query = query.filter(Product.name.ilike(f"%{search[:80]}%"))
    if category: query = query.filter(Product.category == category)
    if vegan: query = query.filter(Product.vegan.is_(True))
    if fragrance_free: query = query.filter(Product.fragrance_free.is_(True))
    return ok([product_json(item, user) for item in query.order_by(Product.name).all()])

@app.get("/api/products/{product_id:int}")
def product_details(product_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    item = db.get(Product, product_id)
    if not item: raise HTTPException(404, detail={"code": "PRODUCT_NOT_FOUND", "message": "Product not found."})
    return ok(product_json(item, user))

@app.get("/api/recommendations/{analysis_id}")
def recommendations(analysis_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    item = db.query(SkinAnalysis).filter_by(id=analysis_id, user_id=user.id).first()
    if not item: raise HTTPException(404, detail={"code": "ANALYSIS_NOT_FOUND", "message": "Analysis not found."})
    ranked = []
    for product in db.query(Product).filter_by(availability=True).all():
        rank = rank_product(product, item.skin_type_estimate, item.observations, user.profile)
        if rank["score"]: ranked.append({**product_json(product, user), "match_score": rank["score"], "reasons": rank["reasons"]})
    return ok(sorted(ranked, key=lambda value: value["match_score"], reverse=True))

@app.post("/api/products/{product_id:int}/save")
def save_product(product_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    if not db.get(Product, product_id): raise HTTPException(404, detail={"code": "PRODUCT_NOT_FOUND", "message": "Product not found."})
    if not db.query(SavedProduct).filter_by(user_id=user.id, product_id=product_id).first():
        db.add(SavedProduct(user_id=user.id, product_id=product_id)); db.commit()
    return ok({}, "Product saved")

@app.delete("/api/products/{product_id:int}/save")
def unsave_product(product_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    db.query(SavedProduct).filter_by(user_id=user.id, product_id=product_id).delete(); db.commit()
    return ok({}, "Product removed")

@app.get("/api/products/saved")
def saved_products(db: Session = Depends(get_db), user=Depends(current_user)):
    items = db.query(Product).join(SavedProduct).filter(SavedProduct.user_id == user.id).all()
    return ok([product_json(item, user) for item in items])

@app.delete("/api/privacy/history")
def delete_history(db: Session = Depends(get_db), user=Depends(current_user)):
    db.query(SkinAnalysis).filter_by(user_id=user.id).delete(); db.commit()
    for path in UPLOAD_DIR.glob(f"{user.id}_*.image"): path.unlink(missing_ok=True)
    return ok({}, "Analysis history and private images deleted")

@app.delete("/api/privacy/account")
def delete_account(db: Session = Depends(get_db), user=Depends(current_user)):
    user_id = user.id
    db.delete(user); db.commit()
    for path in UPLOAD_DIR.glob(f"{user_id}_*.image"): path.unlink(missing_ok=True)
    return ok({}, "Account and associated data deleted")