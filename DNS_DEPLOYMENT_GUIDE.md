# DNS & Deployment Configuration Guide

## Current Setup Overview

### Domain: relayx.tech
- **Registrar**: Your domain registrar (where you manage DNS)
- **Frontend**: Vercel (www.relayx.tech)
- **Backend**: Railway (api.relayx.tech)

## DNS Configuration Required

### Step 1: Update DNS Records at Your Domain Registrar

**Remove:**
- ❌ A Record for `relayx.tech` pointing to `216.198.79.1`

**Keep/Add These Records:**

#### For Frontend (Vercel):
```
Type: CNAME
Name: www
Value: 599ad3263f43ea75.vercel-dns-017.com
TTL: Auto
Status: ✓ Already configured
```

```
Type: CNAME  
Name: @ (or relayx.tech)
Value: cname.vercel-dns.com
TTL: Auto
Status: ⚠️ NEEDS UPDATE (replace the A record)
```

#### For Backend (Railway):
```
Type: CNAME
Name: api
Value: smirhew.up.railway.app
TTL: Auto
Status: ✓ Already configured
```

### Step 2: Configure Vercel Domain Settings

1. Go to your Vercel project dashboard
2. Click **Settings** → **Domains**
3. Add both domains:
   - `www.relayx.tech` (already added ✓)
   - `relayx.tech` (add this)
4. Set redirect:
   - Option A: Redirect `relayx.tech` → `www.relayx.tech` (Recommended)
   - Option B: Redirect `www.relayx.tech` → `relayx.tech`

### Step 3: Configure Vercel Environment Variables

1. In Vercel dashboard → **Settings** → **Environment Variables**
2. Add:
   ```
   Name: VITE_API_URL
   Value: https://api.relayx.tech
   Environment: Production
   ```
3. **Redeploy** your application after adding the variable

### Step 4: Configure Railway Environment Variables

Ensure these are set in Railway:
```
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_number
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
GROQ_API_KEY=your_groq_key
VOICE_GATEWAY_URL=your_voice_gateway_url
CAL_API_KEY=your_cal_api_key
REDIS_URL=your_redis_url (if using external Redis)
```

### Step 5: Test Your Configuration

After DNS propagation (can take 5 minutes to 48 hours):

1. **Test www.relayx.tech:**
   ```
   curl -I https://www.relayx.tech
   ```
   Should return: `HTTP/2 200` with valid SSL certificate

2. **Test api.relayx.tech:**
   ```
   curl https://api.relayx.tech/health
   ```
   Should return: JSON response from your backend

3. **Test in browser:**
   - Visit https://www.relayx.tech (should load frontend with HTTPS)
   - Visit https://relayx.tech (should redirect to www)
   - Open browser DevTools → Network tab
   - Verify API calls go to `https://api.relayx.tech`

## Common Issues & Solutions

### Issue 1: "Invalid Configuration" in Vercel
**Cause:** A record pointing to IP instead of CNAME
**Solution:** Replace A record with CNAME to `cname.vercel-dns.com`

### Issue 2: "Unsecure Site" Warning
**Cause:** Frontend trying to use HTTP instead of HTTPS
**Solution:** 
1. Set `VITE_API_URL=https://api.relayx.tech` in Vercel
2. Redeploy frontend

### Issue 3: CORS Errors
**Cause:** Backend not allowing frontend domain
**Solution:** Backend already updated to allow:
- https://relayx.tech
- https://www.relayx.tech

### Issue 4: API Requests Failing
**Cause:** Frontend still pointing to localhost
**Solution:** Set Vercel environment variable and redeploy

### Issue 5: SSL Certificate Error
**Cause:** DNS not fully propagated or Vercel cert not issued
**Solution:** 
1. Wait 5-30 minutes after DNS changes
2. In Vercel, click "Refresh" next to domain
3. Check "Learn more" link for domain verification status

## DNS Propagation Check

Use these tools to verify DNS changes:
- https://dnschecker.org/
- https://www.whatsmydns.net/

Enter your domain and check:
- `www.relayx.tech` should show Vercel CNAME
- `api.relayx.tech` should show Railway CNAME
- `relayx.tech` should show Vercel CNAME (not an A record)

## Deployment Checklist

### Frontend (Vercel)
- [ ] Environment variable `VITE_API_URL` set to `https://api.relayx.tech`
- [ ] Both `relayx.tech` and `www.relayx.tech` added as domains
- [ ] SSL certificates showing as "Valid"
- [ ] Redirection configured (www ↔ non-www)
- [ ] Application redeployed after env variable change

### Backend (Railway)
- [ ] All environment variables configured
- [ ] CORS updated to allow frontend domains
- [ ] Health endpoint accessible at `https://api.relayx.tech/health`
- [ ] SSL certificate valid

### DNS
- [ ] CNAME for `www.relayx.tech` → Vercel
- [ ] CNAME for `relayx.tech` → Vercel (not A record)
- [ ] CNAME for `api.relayx.tech` → Railway
- [ ] TTL set appropriately (300-3600 seconds)
- [ ] Changes propagated (check with DNS checker tools)

## Architecture Diagram

```
User Browser
     ↓
     ↓ (HTTPS)
     ↓
┌────▼─────────────────────┐
│  www.relayx.tech         │
│  (Vercel - Frontend)     │
│  React + Vite            │
└────┬─────────────────────┘
     │
     │ API Calls (HTTPS)
     │
┌────▼─────────────────────┐
│  api.relayx.tech         │
│  (Railway - Backend)     │
│  FastAPI + Python        │
└────┬─────────────────────┘
     │
     ├─→ Supabase (Database)
     ├─→ Twilio (Voice)
     ├─→ Groq (AI/STT)
     └─→ Cal.com (Scheduling)
```

## Next Steps After Configuration

1. **Monitor Logs:**
   - Railway: Check application logs for any errors
   - Vercel: Check build and function logs
   - Browser DevTools: Monitor network requests

2. **Test All Features:**
   - User registration/login
   - Agent creation
   - Campaign creation
   - Call initiation
   - Dashboard statistics

3. **Performance:**
   - Enable Vercel Analytics (optional)
   - Monitor Railway metrics
   - Set up error tracking (Sentry, etc.)

4. **Backup:**
   - Regular Supabase backups
   - Keep environment variables documented securely

## Support & Resources

- **Vercel Docs**: https://vercel.com/docs/concepts/projects/domains
- **Railway Docs**: https://docs.railway.app/deploy/deployments
- **DNS Guide**: https://www.cloudflare.com/learning/dns/dns-records/
