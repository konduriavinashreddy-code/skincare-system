# Simple Deployment Guide

This guide shows you how to deploy the frontend to Vercel and backend to Render/Railway separately.

## Step 1: Deploy Frontend to Vercel

1. **Move to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Deploy to Vercel**:
   ```bash
   vercel login
   vercel
   ```

3. **Follow the prompts**:
   - Set project name
   - Confirm settings
   - Deploy

4. **Copy your Vercel URL** (e.g., `https://your-app.vercel.app`)

## Step 2: Deploy Backend to Render (Free)

1. **Create a `render.yaml` file in backend directory**:
   ```yaml
   services:
     - type: web
       name: dermacare-backend
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
       envVars:
         - key: DATABASE_URL
           value: sqlite:///./dermacare.db
         - key: JWT_SECRET
           generateValue: true
         - key: AI_MODE
           value: mock
         - key: CORS_ORIGINS
           value: https://your-frontend-url.vercel.app
         - key: UPLOAD_DIR
           value: ./uploads
         - key: MAX_UPLOAD_MB
           value: 8
   ```

2. **Push to GitHub** with the backend code

3. **Go to [render.com](https://render.com)** and:
   - Sign up/login
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repository
   - Select the `backend` folder as root directory
   - Click "Deploy"

4. **Copy your Render URL** (e.g., `https://your-backend.onrender.com`)

## Step 3: Connect Frontend to Backend

1. **Update frontend `.env.production`**:
   ```bash
   cd frontend
   echo "VITE_API_URL=https://your-backend-url.onrender.com/api" > .env.production
   ```

2. **Push changes to Git**

3. **Redeploy frontend on Vercel** (it will auto-deploy or you can trigger manually)

## Alternative: Deploy Backend to Railway

1. **Go to [railway.app](https://railway.app)**

2. **Create a new project**

3. **Deploy from GitHub**:
   - Select your repository
   - Set root directory to `backend`
   - Configure environment variables:
     - `DATABASE_URL`: Use Railway's PostgreSQL
     - `JWT_SECRET`: Generate a random string
     - `AI_MODE`: `mock`
     - `CORS_ORIGINS`: Your Vercel frontend URL
     - `UPLOAD_DIR`: `./uploads`
     - `MAX_UPLOAD_MB`: `8`

4. **Deploy and copy the URL**

## Step 4: Update Frontend API URL

After you have your backend URL, update the frontend:

```bash
cd frontend
# Replace with your actual backend URL
echo "VITE_API_URL=https://your-backend-url.onrender.com/api" > .env.production
git add .env.production
git commit -m "Update backend API URL"
git push
```

Vercel will automatically redeploy with the new backend URL.

## Quick Test

1. Visit your frontend URL
2. Try registering an account
3. Verify it connects to the backend

## Notes

- **Vercel Frontend**: Free tier available
- **Render Backend**: Free tier available (with cold starts)
- **Railway Backend**: Free trial available ($5 credit)
- For production, consider using a proper database (PostgreSQL) instead of SQLite
