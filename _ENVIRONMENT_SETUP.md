# Vercel Environment Variables

After deploying to Vercel, you need to configure these environment variables in your Vercel project settings:

## Required Environment Variables

1. **DATABASE_URL**
   - For Vercel Postgres: Get from your Vercel Postgres dashboard
   - Format: `postgresql://user:password@host:port/database`

2. **JWT_SECRET**
   - Generate a secure random string (min 32 characters)
   - Example: `openssl rand -base64 32`

3. **AI_MODE**
   - Set to `mock` for development
   - Set to `real` when ML model is deployed

4. **CORS_ORIGINS**
   - Your deployed frontend URL
   - Example: `https://your-project.vercel.app`

5. **UPLOAD_DIR**
   - Set to `/tmp/uploads` for Vercel serverless

6. **MAX_UPLOAD_MB**
   - Set to `8` (or your preferred limit)

## Optional Environment Variables

- **MODEL_PATH**: Path to ML model (if using real AI mode)
