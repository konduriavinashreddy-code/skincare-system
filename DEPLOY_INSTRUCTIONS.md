# Deploy to Vercel - Complete Project

This project is now configured to deploy both frontend and backend together on Vercel as a single project.

## Project Structure

```
project/
├── api/                    ← Backend (Vercel serverless functions)
│   ├── app/
│   ├── index.py           ← Serverless entry point
│   └── requirements.txt
├── frontend/               ← Frontend (React/Vite)
│   ├── dist/              ← Built frontend
│   ├── package.json
│   └── vercel.json
├── vercel.json             ← Root configuration
└── .vercelignore           ← Ignores duplicate files
```

## Deployment Steps

### 1. Deploy to Vercel

**Option A: Vercel CLI**
```bash
vercel login
vercel
```

**Option B: Vercel Dashboard**
1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your Git repository
4. Click "Deploy"

### 2. Configure Environment Variables

After deployment, go to your Vercel project **Settings > Environment Variables** and add:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `sqlite:///./dermacare.db` (for testing) or Vercel Postgres URL |
| `JWT_SECRET` | Generate: `openssl rand -base64 32` |
| `AI_MODE` | `mock` |
| `CORS_ORIGINS` | `*` |
| `UPLOAD_DIR` | `/tmp/uploads` |
| `MAX_UPLOAD_MB` | `8` |

### 3. Redeploy

After adding environment variables, redeploy:
```bash
vercel --prod
```

Or trigger a new deployment from the Vercel dashboard.

## How It Works

- **Frontend**: Built as static files in `frontend/dist`
- **Backend**: Deployed as Vercel serverless functions in `api/`
- **Routing**: `/api/*` requests go to Python functions, everything else serves the frontend
- **Single Project**: Both deploy together on Vercel

## Important Notes

### Database
- For testing: SQLite works but data may not persist reliably in serverless
- For production: Use Vercel Postgres or external PostgreSQL

### Serverless Limitations
- Max execution time: 60 seconds (free tier)
- Max request size: 4.5 MB
- Cold starts: First request may be slower
- File uploads: Use `/tmp` directory (ephemeral)

### Upload Storage
The `/tmp/uploads` directory is cleared between function invocations. For persistent storage, consider:
- Vercel Blob Storage
- AWS S3
- Cloudflare R2

## Troubleshooting

### Build Errors
- Ensure `api/requirements.txt` exists
- Check Python version compatibility (3.11+)
- Verify `frontend/package.json` exists

### Runtime Errors
- Check environment variables are set
- Verify database connection
- Check Vercel function logs

### CORS Errors
- Set `CORS_ORIGINS` to `*` for testing
- Or set to your specific domain for production

## Verification

After deployment:
1. Visit your Vercel URL
2. Try registering an account
3. Test the skin analysis feature
4. Verify products load correctly
