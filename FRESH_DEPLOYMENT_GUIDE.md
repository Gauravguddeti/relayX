# 🚀 RelayX Fresh Deployment Guide

Complete step-by-step guide to deploy RelayX from scratch.

---

## 📋 Prerequisites

Before starting, have these ready:
- [ ] Domain name (e.g., relayx.tech)
- [ ] GitHub account
- [ ] Vercel account (free)
- [ ] Railway account (free trial)
- [ ] Supabase project
- [ ] Twilio account with phone number
- [ ] Groq API key (free)
- [ ] Cal.com API key (optional)

---

## Step 1: Setup Supabase Database

### 1.1 Create Supabase Project
1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Name it `relayx` and set a strong password
4. Wait for database to be ready (2-3 minutes)

### 1.2 Run Database Schema
1. In Supabase dashboard → SQL Editor
2. Copy contents from `db/schema.sql`
3. Paste and click "Run"
4. Verify tables created: users, agents, calls, transcripts, contacts, campaigns, etc.

### 1.3 Get Credentials
1. Go to Project Settings → API
2. Copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **Anon/Public Key**: `eyJhbGci...`

---

## Step 2: Deploy Frontend to Vercel

### 2.1 Push Code to GitHub
```powershell
cd D:\projects\relayx\relayX
git add .
git commit -m "Initial deployment"
git push origin main
```

### 2.2 Deploy to Vercel
1. Go to https://vercel.com/new
2. Import your GitHub repository
3. **IMPORTANT:** First set **Root Directory** to `frontend` and click "Edit" to confirm
4. Configure:
   - **Framework Preset**: Select "Vite" from dropdown (ignore FastAPI detection)
   - **Root Directory**: `frontend` ✅ (already set)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

> **Note:** Vercel may detect FastAPI because there's a backend folder in the repo. Ignore this - we're only deploying the frontend. Setting the Root Directory to `frontend` first tells Vercel to look only in that folder.

5. Click "Deploy" and wait (2-3 minutes)

### 2.3 Add Custom Domain
1. In Vercel project → Settings → Domains
2. Add your domain: `relayx.tech`
3. Vercel will show DNS records you need:
   ```
   Type: A
   Name: @
   Value: 76.76.21.21
   
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

### 2.4 Configure DNS (at your domain registrar)
1. Go to your domain registrar (e.g., GoDaddy, Namecheap, Cloudflare)
2. Find DNS Settings
3. Add the records Vercel provided
4. Wait 5-30 minutes for propagation

### 2.5 Add Environment Variables
1. In Vercel → Settings → Environment Variables
2. Add these:
   ```
   VITE_API_URL=https://api.relayx.tech
   VITE_SUPABASE_URL=https://xxxxx.supabase.co
   VITE_SUPABASE_ANON_KEY=eyJhbGci...
   ```
3. **Important:** Click "Redeploy" in Deployments tab

---

## Step 3: Deploy Backend to Railway

### 3.1 Create Railway Project
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-deploy (it may start building immediately)

> **Note:** Railway often auto-deploys on first connection. This is fine - we'll configure it properly in the next step.

### 3.2 Configure Build Settings (IMPORTANT!)
Railway probably deployed from the wrong directory. Fix this:

1. Click on your Railway project/service
2. Go to **Settings** tab
3. Scroll to **Service Settings** section
4. Set these values:
   - **Root Directory**: `backend` ← **CRITICAL - Set this!**
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
5. Click **"Save"** or the values will auto-save
6. Railway will automatically **redeploy** with correct settings

**To verify it's using the right directory:**
- Go to **Deployments** tab
- Click the latest deployment
- Check **Logs** - should show "Uvicorn running" not "No build command"

### 3.3 Add Environment Variables
In Railway → Variables tab, add:

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci... (service_role key from Supabase)

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890

# AI Services
GROQ_API_KEY=gsk_xxxxx
SARVAM_API_KEY=xxxxx (for Indian voices, optional)

# Voice Gateway
VOICE_GATEWAY_URL=https://your-voice-gateway.trycloudflare.com

# Cal.com (optional)
CAL_API_KEY=cal_xxxxx

# Security
JWT_SECRET=generate-a-random-32-char-string
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-secure-password

# CORS
CORS_ORIGINS=https://relayx.tech,https://www.relayx.tech

# Redis (optional, Railway provides)
REDIS_URL=${{REDIS.REDIS_URL}}
```

### 3.4 Add Custom Domain
1. In Railway → Settings → Networking
2. Click "Generate Domain" (you get `xxxxx.up.railway.app`)
3. Add custom domain: `api.relayx.tech`
4. Railway will show DNS record:
   ```
   Type: CNAME
   Name: api
   Value: xxxxx.up.railway.app
   ```

### 3.5 Update DNS
1. Go back to your domain registrar
2. Add the CNAME record for `api.relayx.tech`
3. Wait 5-30 minutes

### 3.6 Test Backend
```powershell
curl https://api.relayx.tech/health
# Should return: {"status": "ok"}
```

---

## Step 4: Setup Voice Gateway (Cloudflare Tunnel)

### 4.1 Install Cloudflared (Windows)
```powershell
# Download
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "$env:USERPROFILE\Downloads\cloudflared.exe"

# Install to Program Files
New-Item -ItemType Directory -Force -Path "C:\Program Files\cloudflared"
Move-Item "$env:USERPROFILE\Downloads\cloudflared.exe" "C:\Program Files\cloudflared\cloudflared.exe"

# Add to PATH
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\cloudflared", "Machine")

# Restart PowerShell for PATH to take effect
```

### 4.2 Start Voice Gateway Locally
```powershell
cd D:\projects\relayx\relayX
cd voice_gateway
pip install -r requirements.txt
python voice_gateway.py
```

### 4.3 Create Cloudflare Tunnel (Quick - No Account)
```powershell
# In a new PowerShell window
cloudflared tunnel --url http://localhost:8001
```

You'll see output like:
```
Your quick Tunnel has been created! Visit it at:
https://random-words-1234.trycloudflare.com
```

**Copy this URL!**

### 4.4 Update Railway Backend
1. Go to Railway → Variables
2. Update `VOICE_GATEWAY_URL` to your tunnel URL:
   ```
   VOICE_GATEWAY_URL=https://random-words-1234.trycloudflare.com
   ```
3. Redeploy backend

### 4.5 Update Twilio Webhook
1. Go to Twilio Console → Phone Numbers
2. Select your phone number
3. Under "Voice & Fax" → "A Call Comes In":
   ```
   Webhook: https://api.relayx.tech/api/calls/voice
   HTTP Method: POST
   ```
4. Save

---

## Step 5: Final Configuration & Testing

### 5.1 Update Frontend Environment Variables
Go back to Vercel and ensure these are set:
```
VITE_API_URL=https://api.relayx.tech
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

Redeploy frontend if you changed anything.

### 5.2 Create First User
1. Visit https://relayx.tech/signup
2. Sign up with email/password
3. Or use test credentials if you have them

### 5.3 Test the System

**Test 1: Frontend loads**
```
Visit: https://relayx.tech
Expected: Landing page loads with animations
```

**Test 2: Backend health**
```powershell
curl https://api.relayx.tech/health
# Expected: {"status":"ok"}
```

**Test 3: Login works**
```
Visit: https://relayx.tech/login
Login with your credentials
Expected: Redirects to /dashboard
```

**Test 4: Make a test call**
1. Go to Dashboard
2. Click "New Call" or "Test Call"
3. Enter your phone number
4. Should receive AI call within 10 seconds

---

## Step 6: Production Hardening (Optional)

### 6.1 Enable Supabase RLS (Row Level Security)
```sql
-- In Supabase SQL Editor
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;

-- Add policies (example)
CREATE POLICY "Users can view own data" ON users
  FOR SELECT USING (auth.uid() = id);
```

### 6.2 Setup Monitoring
1. **Vercel**: Analytics → Enable Web Analytics
2. **Railway**: Metrics tab shows CPU, memory, requests
3. **Supabase**: Database → Logs

### 6.3 Setup Permanent Cloudflare Tunnel
See [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md) for permanent tunnel with custom domain.

### 6.4 Enable Rate Limiting
Backend already has rate limiting via `limiter.py`. Configure in Railway:
```
RATE_LIMIT_ENABLED=true
RATE_LIMIT_CALLS_PER_MINUTE=10
```

---

## 🎯 Quick Checklist

### DNS Configuration
- [ ] A record for `relayx.tech` → Vercel IP
- [ ] CNAME for `www.relayx.tech` → `cname.vercel-dns.com`
- [ ] CNAME for `api.relayx.tech` → Railway URL

### Vercel (Frontend)
- [ ] Repository connected
- [ ] Root directory: `frontend`
- [ ] Environment variables set
- [ ] Custom domain added
- [ ] SSL certificate issued
- [ ] Latest deployment successful

### Railway (Backend)
- [ ] Repository connected
- [ ] Root directory: `backend`
- [ ] All environment variables set
- [ ] Custom domain added
- [ ] Health check passing
- [ ] Logs show no errors

### Voice Gateway
- [ ] Voice gateway running locally
- [ ] Cloudflare tunnel active
- [ ] Tunnel URL set in Railway
- [ ] Twilio webhook configured
- [ ] Test call successful

### Supabase
- [ ] Database schema loaded
- [ ] Tables created successfully
- [ ] API keys copied to Vercel & Railway
- [ ] Connection test passed

---

## 🔥 Common Issues & Fixes

### Issue: "Cannot connect to API"
**Fix:**
1. Check Vercel env var: `VITE_API_URL=https://api.relayx.tech`
2. Redeploy frontend
3. Clear browser cache

### Issue: "502 Bad Gateway on API"
**Fix:**
1. Check Railway logs for errors
2. Verify all environment variables are set
3. Restart Railway service

### Issue: "Voice Gateway not reachable"
**Fix:**
1. Ensure voice_gateway.py is running
2. Check cloudflared tunnel is active
3. Update VOICE_GATEWAY_URL in Railway
4. Check firewall isn't blocking port 8001

### Issue: "CORS error"
**Fix:**
1. In Railway, check `CORS_ORIGINS` includes your frontend URL
2. Must include both `https://relayx.tech` and `https://www.relayx.tech`

### Issue: "Database connection failed"
**Fix:**
1. Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in Railway
2. Check Supabase project is active (not paused)
3. Test connection from Railway logs

---

## 📞 Support

If you need help:
1. Check Railway logs: `railway logs`
2. Check Vercel deployment logs
3. Check browser console (F12) for frontend errors
4. Review this guide again step by step

---

## 🎉 Success!

Once everything is green:
- ✅ Frontend: https://relayx.tech
- ✅ Backend: https://api.relayx.tech
- ✅ Voice Gateway: Active tunnel
- ✅ Database: Connected
- ✅ Test calls working

You're now live in production! 🚀
