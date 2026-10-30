# Deploy Frontend + Backend on Vercel (Single Project)

This guide shows you how to deploy both the frontend and backend together on Vercel as a single project.

## Prerequisites

1. Vercel account (free tier works)
2. Git repository with this code
3. Vercel Postgres database (recommended for production)

## Step 1: Set Up Vercel Postgres (Optional but Recommended)

1. Go to [vercel.com](https://vercel.com) and sign in
2. Create a new project or use an existing one
3. Go to the "Storage" tab
4. Click "Create Database" > "Postgres"
5. Choose a region
6. Copy the `DATABASE_URL` from the database settings

## Step 2: Configure Environment Variables

In your Vercel project dashboard, go to **Settings > Environment Variables** and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | (from Vercel Postgres or `sqlite:///./dermacare.db` for testing) | Database connection string |
| `JWT_SECRET` | Generate with `openssl rand -base64 32` | Secret for JWT tokens |
| `AI_MODE` | `mock` | Use mock AI (set to `real` when ML model is ready) |
| `CORS_ORIGINS` | `*` or your domain | Allow all origins for now |
| `UPLOAD_DIR` | `/tmp/uploads` | Upload directory for serverless |
| `MAX_UPLOAD_MB` | `8` | Max upload size |

**Quick way to generate JWT_SECRET:**
```bash
openssl rand -base64 32
```

## Step 3: Deploy to Vercel

### Option A: Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from project root
vercel
```

Follow the prompts:
- Set project name
- Confirm settings
- Deploy

### Option B: Using Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your Git repository
4. Vercel will auto-detect the configuration from `vercel.json`
5. Click "Deploy"

## Step 4: Verify Deployment

1. Visit your deployed URL (e.g., `https://your-project.vercel.app`)
2. Try registering a new account
3. Test the skin analysis feature
4. Check that products load correctly

## How It Works

- **Frontend**: React app built and served as static files
- **Backend**: FastAPI converted to Vercel serverless functions using Mangum
- **API Routes**: `/api/*` requests are routed to the Python serverless function
- **Static Files**: All other requests serve the React frontend

## Important Notes

### Database
- For testing: Use SQLite (`DATABASE_URL=sqlite:///./dermacare.db`)
- For production: Use Vercel Postgres or external PostgreSQL
- **Note**: SQLite in serverless functions may have issues with file persistence

### Serverless Limitations
- Max execution time: 60 seconds (free tier)
- Max request size: 4.5 MB
- Cold starts: First request may be slower
- File uploads: Use `/tmp` directory (ephemeral)

### Upload Directory
Serverless functions use `/tmp/uploads` which is cleared between function invocations. For persistent storage, consider:
- Vercel Blob Storage
- AWS S3
- Cloudflare R2

## Troubleshooting

### Build Errors

**Error**: `npm install` fails
- Check that `frontend/package.json` exists
- Verify Node.js version (18+ recommended)

**Error**: Python build fails
- Check that `api/requirements.txt` exists
- Verify Python version (3.11+ recommended)

### Runtime Errors

**Error**: Database connection fails
- Verify `DATABASE_URL` is set correctly
- Check database is accessible from Vercel
- For SQLite, this may not work reliably in serverless

**Error**: CORS errors
- Verify `CORS_ORIGINS` includes your domain
- Set to `*` for testing

**Error**: Upload fails
- Check file size is under 4.5 MB
- Verify `UPLOAD_DIR` is set to `/tmp/uploads`

### 500 Errors

Check Vercel function logs:
1. Go to your Vercel project
2. Click the "Functions" tab
3. View logs for `/api` function

## Post-Deployment Checklist

- [ ] Frontend loads correctly
- [ ] Registration works
- [ ] Login works
- [ ] API endpoints respond
- [ ] File uploads work (if needed)
- [ ] Database persists data
- [ ] Environment variables are set for production

## Next Steps for Production

1. **Upgrade Database**: Move from SQLite to Vercel Postgres
2. **Add Custom Domain**: Set up a custom domain in Vercel
3. **Monitor Performance**: Use Vercel Analytics
4. **Set Up Alerts**: Configure error monitoring
5. **Upgrade Plan**: Consider Vercel Pro for longer function timeouts
