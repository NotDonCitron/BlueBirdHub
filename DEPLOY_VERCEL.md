# ▲ Deploy OrdnungsHub to Vercel

## Quick Deploy (3 minutes)

### Prerequisites
- GitHub account
- Vercel account (free at [vercel.com](https://vercel.com))

### Step 1: Install Vercel CLI
```bash
npm i -g vercel
```

### Step 2: Deploy
```bash
# In your project directory
vercel

# Follow the prompts:
# - Link to existing project? No
# - What's your project name? ordnungshub
# - Which directory? . (current)
# - Override settings? No
```

### Step 3: Configure Environment Variables

In Vercel Dashboard:
1. Go to your project settings
2. Navigate to "Environment Variables"
3. Add:

```env
# Required
SECRET_KEY=generate-a-secure-key
DATABASE_URL=your-database-url

# Optional
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
ENABLE_METRICS=true
```

### Step 4: Set Up Database

Since Vercel is serverless, use:
- **Vercel Postgres** (built-in)
- **Supabase** (free tier)
- **PlanetScale** (MySQL)
- **Neon** (PostgreSQL)

### Your App URLs

- **API**: `https://ordnungshub.vercel.app/api/`
- **Docs**: `https://ordnungshub.vercel.app/docs`
- **Health**: `https://ordnungshub.vercel.app/health`

## 🎉 Deployed in under 3 minutes!