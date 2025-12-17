# Move Docker to D Drive (Manual Steps)

Your C drive has **56MB free** and Docker is using **40.7GB**. Here's how to move it:

## Option 1: Docker Desktop Settings (Easiest)

1. **Open Docker Desktop**
2. Click the **Settings (gear icon)**
3. Go to **Resources** → **Advanced**
4. Look for **"Disk image location"** or **"Docker data directory"**
5. Click **"Browse"** and select `D:\DockerData`
6. Click **"Apply & Restart"**

**If that option doesn't exist, use Option 2:**

---

## Option 2: Manual WSL Export/Import

### Step 1: Completely Stop Docker
```powershell
# Close Docker Desktop from system tray (right-click → Quit Docker Desktop)
wsl --shutdown
```

### Step 2: Export docker-desktop-data
```powershell
wsl --export docker-desktop-data D:\DockerData\docker-desktop-data.tar
```
*This will take 3-5 minutes. The file will be ~40GB.*

### Step 3: Unregister from C drive
```powershell
wsl --unregister docker-desktop-data
```

### Step 4: Import to D drive
```powershell
wsl --import docker-desktop-data D:\DockerData\docker-desktop-data D:\DockerData\docker-desktop-data.tar --version 2
```

### Step 5: Clean up
```powershell
Remove-Item D:\DockerData\docker-desktop-data.tar
```

### Step 6: Restart Docker Desktop
Open Docker Desktop and it should now use D drive.

---

## Option 3: Easiest - Just Reset Docker (Loses all containers/images)

1. **Open Docker Desktop**
2. Go to **Settings** → **Troubleshoot**
3. Click **"Clean / Purge data"** or **"Reset to factory defaults"**
4. **BEFORE clicking Reset:**
   - Go to `C:\Users\Nihal\.docker\` 
   - Create a file called `daemon.json` with:
   ```json
   {
     "data-root": "D:\\DockerData"
   }
   ```
5. Now click **Reset**
6. Docker will restart and use D drive

---

## Current Status
- **C Drive Free:** 56MB 💀
- **Docker Size:** 40.7GB
- **D Drive Free:** 93GB ✅

Pick whichever option works for you!
