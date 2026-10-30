# Vercel Deployment Guide

This guide will help you deploy the DermaCare AI application to Vercel.

## Prerequisites

1. A Vercel account (free tier works)
2. Git repository with this code
3. Vercel Postgres database (recommended) or external PostgreSQL

## Step 1: Deploy to Vercel

### Option A: Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from the project root
vercel
```

### Option B: Using Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your Git repository
4. Vercel will auto-detect the configuration

## Step 2: Set Up Vercel Postgres

1. In your Vercel project dashboard, go to the "Storage" tab
2. Click "Create Database"
3. Select "Postgres"
4. Choose a region close to your users
5. Copy the `DATABASE_URL` from the database settings

## Step 3: Configure Environment Variables

In your Vercel project dashboard, go to Settings > Environment Variables and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | (from Vercel Postgres) | PostgreSQL connection string |
| `JWT_SECRET` | (generate one) | Use `openssl rand -base64 32` |
| `AI_MODE` | `mock` | Set to `real` when ML model is ready |
| `CORS_ORIGINS` | `https://your-project.vercel.app` | Your deployed frontend URL |
| `UPLOAD_DIR` | `/tmp/uploads` | Upload directory for serverless |
| `MAX_UPLOAD_MB` | `8` | Max upload size in MB |

## Step 4: Deploy

1. Push your changes to Git
2. Vercel will automatically deploy
3. Wait for the build to complete
4. Access your app at `https://your-project.vercel.app`

## Step 5: Test the Deployment

1. Visit your deployed URL
2. Try registering a new account
3. Test the skin analysis feature
4. Check that products load correctly

## Troubleshooting

### Build Errors

If you encounter build errors:
- Check that all dependencies are in `api/requirements.txt`
- Ensure Python version is compatible (3.11+)
- Verify the API structure is correct

### Database Connection Errors

- Verify `DATABASE_URL` is set correctly
- Check that Vercel Postgres is in the same region as your project
- Ensure the database is not paused

### CORS Errors

- Verify `CORS_ORIGINS` includes your deployed URL
- Check that the frontend is using `/api` as the base URL

### Upload Issues

- Serverless functions have file size limits (4.5MB for Vercel)
- Consider using Vercel Blob Storage for larger files
- Ensure `UPLOAD_DIR` is set to `/tmp/uploads`

## Post-Deployment Checklist

- [ ] Database is accessible from serverless functions
- [ ] Authentication works correctly
- [ ] File uploads function properly
- [ ] Product recommendations load
- [ ] All API endpoints respond correctly
- [ ] Environment variables are configured for production

## Notes

- Serverless functions have a maximum execution time of 60 seconds
- For production, consider upgrading to Vercel Pro for longer timeouts
- Monitor your Vercel dashboard for errors and performance metrics
- Set up a custom domain if needed
