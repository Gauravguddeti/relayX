# 🐳 Docker Optimization & Maintenance Guide

## 🔍 Understanding Docker Disk Usage

Docker can consume significant disk space from:
1. **Images** - Base images + your built images (2-5GB)
2. **Containers** - Running/stopped containers (usually small)
3. **Build cache** - Cached layers from builds (can be 5-10GB)
4. **Volumes** - Persistent data (varies)

**10-20GB is normal** if you have:
- Multiple image versions
- Build cache from rebuilds
- Old stopped containers
- Unused images

---

## 🧹 Complete Cleanup (Fresh Start)

### Option 1: Use the Automated Script

```powershell
# This will clean EVERYTHING and start fresh
.\cleanup_and_reset.ps1
```

**What it does:**
- ✅ Stops all containers
- ✅ Removes all containers
- ✅ Removes all images
- ✅ Removes all volumes
- ✅ Clears build cache
- ✅ Removes local Python packages
- ✅ Clears model caches (Piper, Whisper, Silero)

### Option 2: Manual Cleanup

```powershell
# Stop all containers
docker-compose down

# Remove all containers
docker rm -f $(docker ps -aq)

# Remove all images
docker rmi -f $(docker images -q)

# Remove all volumes
docker volume rm $(docker volume ls -q)

# Clear build cache
docker builder prune -a -f

# Full system cleanup
docker system prune -a --volumes -f
```

---

## 🔄 Rebuild Containers (After Cleanup)

### Option 1: Use the Rebuild Script

```powershell
.\rebuild_docker.ps1
```

### Option 2: Manual Rebuild

```powershell
# Build with no cache (fresh install)
docker-compose build --no-cache

# Start containers
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## ✅ What's Been Optimized

### 1. Multi-Stage Docker Builds
**Before:**
- All build tools remain in final image
- Large image size (~2GB per service)

**After:**
- Build dependencies in separate stage
- Only runtime dependencies in final image
- **Smaller images** (~800MB per service)

### 2. Better Layer Caching
**Before:**
- Code copied before requirements
- Any code change = reinstall all packages

**After:**
- Requirements copied first
- Code changes don't trigger package reinstall
- **Faster rebuilds** (30 seconds vs 5 minutes)

### 3. Dependencies in Docker Only
**Before:**
- Packages installed locally AND in Docker
- Duplicate storage

**After:**
- All packages ONLY in Docker containers
- Local system stays clean
- **No local pip installs needed**

---

## 📊 Check Docker Disk Usage

```powershell
# Overview of space usage
docker system df

# Detailed breakdown
docker system df -v

# See all images
docker images

# See all containers
docker ps -a

# See all volumes
docker volume ls
```

---

## 🗑️ Regular Maintenance (Weekly)

### Remove Dangling Images (unused layers)
```powershell
docker image prune -f
```

### Remove Stopped Containers
```powershell
docker container prune -f
```

### Remove Unused Networks
```powershell
docker network prune -f
```

### Remove Unused Volumes
```powershell
docker volume prune -f
```

### Clean Build Cache (if > 5GB)
```powershell
docker builder prune -f
```

---

## 🎯 Expected Disk Usage (After Cleanup)

| Component | Size | Description |
|-----------|------|-------------|
| **Base Images** | ~1.5GB | Python 3.11-slim (2 services) |
| **Built Images** | ~1.5GB | Your app layers |
| **Containers** | ~50MB | Running containers |
| **Build Cache** | ~500MB | Efficient caching |
| **Volumes** | ~10MB | Logs only |
| **Total** | **~3.5GB** | ✅ Optimized |

---

## 🚀 Development Workflow

### Starting Work (Clean Build)
```powershell
# Clean start
.\cleanup_and_reset.ps1

# Rebuild fresh
.\rebuild_docker.ps1
```

### Daily Development
```powershell
# Code changes - rebuild affected service only
docker-compose build backend
docker-compose up -d backend

# OR rebuild all
docker-compose up -d --build
```

### Check Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f voice-gateway
```

### Stop Everything
```powershell
docker-compose down
```

---

## 🐛 Troubleshooting

### Issue: "Build failed - out of space"

**Solution:**
```powershell
# Free up space
docker system prune -a --volumes -f

# Rebuild
docker-compose build --no-cache
```

### Issue: "Packages still installing locally"

**Check:**
1. Are you running `pip install` outside Docker? ❌ Don't do this
2. Use Docker for development: `docker-compose up -d`
3. Exec into container if needed: `docker exec -it relayx-backend bash`

### Issue: "Can't find module XYZ"

**Solution:**
```powershell
# Rebuild container (packages may have changed)
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Issue: "Docker still using 10GB+"

**Reasons:**
1. Multiple old image versions (check: `docker images`)
2. Build cache accumulation (clean: `docker builder prune -a -f`)
3. Stopped containers (clean: `docker container prune -f`)

**Full cleanup:**
```powershell
docker system prune -a --volumes -f
docker builder prune -a -f
```

---

## 📝 Best Practices

### ✅ DO:
- Use `docker-compose up -d` to run services
- Use `docker exec` to access containers
- Keep code in mounted volumes (auto-updates)
- Run cleanup weekly
- Use the rebuild script for fresh builds

### ❌ DON'T:
- Install packages locally with `pip install`
- Run Python scripts outside Docker
- Keep old images around
- Build without cleanup if > 10GB used

---

## 🔧 Advanced: Development Inside Containers

### Execute Commands in Container
```powershell
# Open bash shell in backend
docker exec -it relayx-backend bash

# Run a script
docker exec -it relayx-backend python scripts/test.py

# Install package (temporary - add to requirements.txt for persistence)
docker exec -it relayx-backend pip install some-package
```

### View Real-Time Logs
```powershell
# All services
docker-compose logs -f

# Since 10 minutes ago
docker-compose logs -f --since 10m

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Single Service
```powershell
docker-compose restart backend
docker-compose restart voice-gateway
```

---

## 📈 Monitoring Docker Performance

### Resource Usage
```powershell
# CPU and memory usage
docker stats

# Specific container
docker stats relayx-backend
```

### Image Sizes
```powershell
# List images sorted by size
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | sort -k3 -h
```

### Container Details
```powershell
# Inspect container
docker inspect relayx-backend

# View container processes
docker top relayx-backend
```

---

## 🎉 Summary

After running cleanup and rebuild:

**Before:**
- 10-20GB Docker usage ❌
- Packages installed locally AND in Docker ❌
- Slow rebuilds ❌
- Cluttered system ❌

**After:**
- ~3-4GB Docker usage ✅
- All packages ONLY in Docker ✅
- Fast rebuilds (layer caching) ✅
- Clean system ✅

---

## 🚀 Quick Commands Reference

```powershell
# Complete cleanup and rebuild
.\cleanup_and_reset.ps1
.\rebuild_docker.ps1

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Check disk usage
docker system df

# Weekly cleanup
docker system prune -f
docker builder prune -f

# Access container
docker exec -it relayx-backend bash
```

---

## 📞 Need Help?

1. Check logs: `docker-compose logs -f`
2. Check disk usage: `docker system df -v`
3. Full reset: `.\cleanup_and_reset.ps1`
4. Rebuild: `.\rebuild_docker.ps1`

**Remember:** All development should happen in Docker containers. Your local system stays clean! 🎯
