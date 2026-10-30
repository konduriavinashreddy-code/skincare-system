# DermaCare AI

An educational skin-care journal with image-based quality checks, cautious visible-characteristic observations, simple routine guidance, and preference-aware product-category suggestions. It is not a diagnostic tool. The project runs locally in an explicitly labeled mock mode without a trained model or marketplace credentials.

## Safety and demo boundaries

> DermaCare AI provides image-based skin-care observations and general product recommendations. It is not a medical diagnostic tool and should not replace professional medical advice.

`AI_MODE=mock` is the default. Its stable, image-hash-derived scores exist only to exercise the application flow; no AI model has assessed the image. The mock always reports low confidence and an undetermined skin type. Do not present mock outputs as research, clinical evidence, or actual user assessment. Model mode calls the separate PyTorch service and returns 503 until a checkpoint exists. A trained checkpoint still requires careful validation, representative consented data, bias assessment, and clinical/regulatory review before real-world use.

The seeded catalog contains invented demo category examples, not real branded listings, ratings, reviews or product claims. These entries are visibly marked demo. Amazon and Flipkart buttons create marketplace **search URLs** from the name; they are not verified product pages, affiliate links, or proof of availability. Exact retailer links should only be added through an approved feed/API or a verified admin catalog workflow.

## Features

- Responsive landing page, registration/login, dashboard, profile preferences, upload/camera capture, real-time image analysis, and a persistent animated assistant chat available from every page. The chat handles skincare questions, guides users through skin type/budget/preferences, and shows catalog-backed product matches in the conversation rather than opening a separate assistant page. Product cards use catalog image URLs when provided and category-specific local illustrations for the seeded demo catalog.
- FastAPI JSON API with PBKDF2-HMAC password hashing, signed JWT access tokens, per-user history, profile settings and data deletion.
- JPG/JPEG, PNG and WEBP content-type, size, decode, resolution, blur, lighting and face-presence checks. OpenCV/Pillow preprocessing is isolated from inference.
- SQLite by default for a quick local backend; PostgreSQL in Compose.
- Separate ResNet-18 transfer-learning multi-head model and training entry point. Training data is not included.
- Product ranking considers observed concern/category alignment, skin type, sensitivity, allergy conflicts, budget and preferences.
- Generated private upload names, non-public local upload directory, CORS configuration and upload size cap.

## Architecture

```text
frontend (React / Vite) -> backend (FastAPI) -> SQLite or PostgreSQL
                                  |-> quality + preprocessing (OpenCV / Pillow)
                                  |-> mock observation adapter, or HTTP -> ml-service (PyTorch)
                                  |-> SQLAlchemy product ranking + marketplace search URLs
```

The frontend communicates with the API; it does not fabricate analysis data. The API persists account/profile/history/product state. Raw photo bytes submitted to `/api/skin/analyze` are processed in memory and are not persisted. The optional `/api/skin/upload` endpoint writes validated bytes into a private local folder with a generated name. There is no public image-serving route.

## Local setup

Requirements: Node.js 20+, Python 3.11+ (3.12 recommended), and npm. A PostgreSQL server is optional for direct local development.

### Backend

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

The default database is `backend/dermacare.db`; database tables and clearly labeled demo products are initialized on startup. API docs are at `http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Set `VITE_API_URL` only if the API is not at `http://localhost:8000/api`. Registration creates a local account; there is no hard-coded demo password. Use an email you control only in a local test environment.

### ML service

The mock flow needs no PyTorch installation. To run model mode, install `ml-service/requirements.txt`, supply a trained checkpoint at `ml-service/models/skin_model.pt`, start the ML API on port 8001, and set backend `AI_MODE=model` and `ML_SERVICE_URL=http://localhost:8001`.

Training CSV columns: `image`, `acne_like_features`, `redness`, `dark_spots`, `oiliness`, `dryness`, `uneven_tone`, `texture`, `fine_lines`, `skin_type`. Use consented and appropriately licensed image data plus qualified labels; none is provided.

```powershell
cd ml-service
pip install -r requirements.txt
python training/train.py --csv datasets/labels.csv --output models/skin_model.pt --epochs 5
uvicorn main:app --reload --port 8001
```

## Docker

From the repository root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The app is available at `http://localhost:5173`, API docs at `http://localhost:8000/docs`. Compose starts PostgreSQL, the FastAPI API, and Vite; the model container is opt-in because CPU PyTorch images are large and mock mode does not need it. Enable it after adding a trained checkpoint with `docker compose --profile model up --build`; set `AI_MODE=model` in `.env` for backend inference. Use unique secrets, TLS, hardened cookies, restricted CORS, persistent encrypted storage and backups before deployment.

## API overview

- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- `GET/PUT /api/profile`
- `POST /api/skin/quality-check`, `/api/skin/upload`, `/api/skin/analyze`, `/api/skin/camera`
- `GET /api/skin/history`, `GET/DELETE /api/skin/analysis/{id}`
- `GET /api/recommendations/{analysis_id}`
- `GET /api/products?search=&category=&vegan=&fragrance_free=`, `GET /api/products/{id}`, `GET /api/products/saved`
- `POST/DELETE /api/products/{id}/save`
- `DELETE /api/privacy/history`, `DELETE /api/privacy/account`

Responses use `{ "success": true, "data": ..., "message": ... }` for successful calls. OpenAPI at `/docs` lists schemas and authorization. Send `Authorization: Bearer <access_token>` for protected calls.

## Database and data lifecycle

SQLAlchemy creates the current schema when the API starts. SQLite is convenient locally; PostgreSQL is used in Docker. Formal Alembic migrations are not yet included. The schema includes users, user profiles, analyses, products and saved products; structured observation and quality details are JSON columns on the analysis record. Account/history deletion endpoints are available. Uploaded image deletion removes files stored by the optional upload endpoint.

## Tests

```powershell
cd backend
pip install -r requirements.txt
pytest -q
```

## Security and privacy notes

Passwords are never stored in plaintext. JWTs expire after 12 hours. This demonstration stores the bearer token in browser local storage; production should use a carefully configured secure, HTTP-only cookie, CSRF protection, HTTPS, key rotation and rate limiting. Configure `JWT_SECRET`, `CORS_ORIGINS`, upload limits and managed storage for your deployment. Add rate limiting, email verification, audit logging, retention policy, malware scanning and database migrations before public use. Images are not used for training. Local uploads are private to the server filesystem; do not mount them to a public static directory.

## Marketplace and product data

Demo records are clearly identified and make no efficacy claims. Search URLs are generic marketplace searches. For deployment, load current product details, prices, availability and verified links from authorized APIs/feeds or careful manual admin entry, record verification timestamps, and respect retailer terms. No scraping or marketplace credentials are included.

## Current limitations and next steps

This is a complete runnable portfolio baseline, not a production clinical system. It does not ship a trained skin model, verified commercial product feed, Alembic migrations, admin product-management UI, Redis/Celery, or marketplace credentials. The mock mode supports end-to-end UI/API demonstrations while making that limitation explicit. The model training script is a starting scaffold, not evidence of model validity.