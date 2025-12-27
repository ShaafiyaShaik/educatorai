# PostgreSQL Setup Guide

## Quick Setup (Choose One Method)

### Method 1: Cloud PostgreSQL (Recommended - Free)

#### Using Supabase (Easiest):
1. Visit https://supabase.com and sign up
2. Create a new project
3. Go to Settings → Database
4. Copy the "Connection String" (URI format)
5. It looks like: `postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres`

#### Using Render.com:
1. Visit https://render.com and sign up
2. New → PostgreSQL
3. Free instance name: `educatorai-db`
4. Copy "External Database URL"

#### Using Railway.app:
1. Visit https://railway.app and sign up
2. New Project → PostgreSQL
3. Copy connection string from Variables tab

### Method 2: Local PostgreSQL

#### On Windows:
```powershell
# Install via Chocolatey
choco install postgresql

# Or download installer from:
# https://www.postgresql.org/download/windows/

# After install, create database:
psql -U postgres
CREATE DATABASE educator_db;
\q
```

#### On Mac:
```bash
# Install via Homebrew
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb educator_db
```

#### On Linux:
```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
sudo -u postgres createdb educator_db
```

## Configure Your App

### 1. Install PostgreSQL driver:
```bash
pip install psycopg2-binary
```

### 2. Set DATABASE_URL

**Option A: Environment Variable (Recommended)**
```bash
# Windows PowerShell
$env:DATABASE_URL="postgresql://username:password@host:port/database"

# Linux/Mac
export DATABASE_URL="postgresql://username:password@host:port/database"
```

**Option B: Create `.env` file**
```env
DATABASE_URL=postgresql://username:password@host:port/database
```

**Option C: Create DEPLOY_DATABASE_URL file**
```bash
echo "postgresql://username:password@host:port/database" > DEPLOY_DATABASE_URL
```

### Connection String Format:
```
postgresql://username:password@hostname:port/database_name

Examples:
- Supabase: postgresql://postgres:yourpass@db.xxx.supabase.co:5432/postgres
- Render: postgresql://user:pass@xxx.render.com:5432/dbname
- Local: postgresql://postgres:postgres@localhost:5432/educator_db
```

## Migrate Data from SQLite to PostgreSQL

### Automatic Migration Script:
```python
# Run this after setting DATABASE_URL
python scripts/migrate_sqlite_to_postgres.py
```

### Manual Steps:
1. Backup SQLite: Copy `educator_db.sqlite`
2. Set DATABASE_URL to PostgreSQL
3. Start app - tables auto-create
4. Run migration script to copy data

## Verify Setup

```python
# Test connection
python -c "from app.core.database import engine; print(engine.url)"
```

## Troubleshooting

### "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Connection refused
- Check hostname/port are correct
- For cloud: Ensure IP is whitelisted (Supabase/Render auto-allow)
- For local: Ensure PostgreSQL service is running

### SSL required
Add `?sslmode=require` to connection string:
```
postgresql://user:pass@host:5432/db?sslmode=require
```

## Production Deployment

For Render.com deployment:
1. Create PostgreSQL database on Render
2. In web service environment variables, add:
   - `DATABASE_URL` = (your PostgreSQL connection string)
3. Deploy - app will auto-use PostgreSQL
