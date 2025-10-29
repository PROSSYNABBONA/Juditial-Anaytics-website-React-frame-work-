# Railway Deployment Guide

## Quick Setup

1. **Push your code to GitHub** (if not already done)
2. **Connect Railway to your GitHub repo**
3. **Set Environment Variables** in Railway dashboard:
   - `DATABASE_URL` - Your MySQL/PostgreSQL connection string
     - Example: `mysql+pymysql://user:password@host:port/database?charset=utf8mb4`
     - Or SQLite: `sqlite:///./judicial.db`
   - `ENV=production` - Set to production mode
   - `JWT_SECRET_KEY` - A random secret for JWT tokens (generate one)
   - `CORS_ORIGINS` - (Optional) Comma-separated origins, defaults to "*" in production

4. **Railway will automatically:**
   - Detect the Dockerfile
   - Build the React frontend
   - Install Python dependencies
   - Deploy everything on a single service

## Environment Variables Summary

```
DATABASE_URL=mysql+pymysql://user:pass@host:3306/judicial_dashboard?charset=utf8mb4
ENV=production
JWT_SECRET_KEY=your-random-secret-key-here
CORS_ORIGINS=https://your-app.railway.app (optional)
```

## Database Options

### Option 1: Railway PostgreSQL (Recommended)
1. Create a PostgreSQL service in Railway
2. Copy the connection string
3. Set `DATABASE_URL` to the PostgreSQL connection string
4. Update `backend/requirements.txt` to include `psycopg2-binary` if needed

### Option 2: External MySQL
- Use your existing MySQL server
- Set `DATABASE_URL` to your MySQL connection string

### Option 3: SQLite (Development only)
- Set `DATABASE_URL=sqlite:///./judicial.db`
- Note: Data may be lost on redeploy unless using persistent volumes

## Troubleshooting

- **Build fails**: Check that all paths in Dockerfile match your directory structure
- **Frontend not loading**: Ensure `ENV=production` is set
- **Database errors**: Verify `DATABASE_URL` format and credentials
- **Port errors**: Railway sets `PORT` automatically, don't override it

## Files Created

- `Dockerfile` - Multi-stage build for React + FastAPI
- `.railwayignore` - Excludes unnecessary files from deployment
- Updated `backend/app/main.py` - Serves React static files in production

