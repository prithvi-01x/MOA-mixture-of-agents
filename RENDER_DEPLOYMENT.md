# Deploying MOA to Render.com

To deploy this Mixture of Agents (MOA) project to [Render](https://render.com), follow these instructions. 

Since this is a monorepo with a FastAPI backend (SQLite database) and a React frontend, you will need two services: a **Web Service** for the backend and a **Static Site** for the frontend.

---

## 1. Backend: FastAPI (Web Service)

### Configuration
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt && pip install gunicorn`
- **Start Command:** `gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
- **Root Directory:** `.` (Keep as root, or adjust if you move files)

### Persistent SQLite Database
Render's filesystem is ephemeral. To keep your conversation history, you **must** attach a persistent disk.
1. Go to **Disks** in your Web Service settings.
2. Click **Add Disk**.
3. Name: `moa-data`
4. Mount Path: `/data`
5. Size: `1 GB` (Free/paid tier depending on your plan)

### Environment Variables
Set these in the **Environment** tab:
- `DB_PATH`: `/data/moa.db`
- `CONFIG_PATH`: `/data/config.json`
- `GROQ_API_KEY`: `your_gsk_key_here`
- `OPENROUTER_API_KEY`: `your_openrouter_key_here` (optional)
- `CORS_ORIGINS`: `https://your-frontend-url.onrender.com` (Add your Static Site URL here once created)

---

## 2. Frontend: React + Vite (Static Site)

### Configuration
- **Runtime:** `Static Site`
- **Build Command:** `pnpm install && pnpm build` (Ensure `pnpm` is available or use `npm install && npm run build`)
- **Publish Directory:** `frontend/dist`
- **Root Directory:** `.`

### Environment Variables
Set these in the **Environment** tab:
- `VITE_API_URL`: `https://your-backend-url.onrender.com` (The URL of your FastAPI Web Service)

---

## 3. Infrastructure as Code (Optional)

You can use a `render.yaml` file in the root of your repo to deploy both services automatically:

```yaml
services:
  # --- Backend ---
  - type: web
    name: moa-backend
    env: python
    buildCommand: pip install -r requirements.txt && pip install gunicorn
    startCommand: gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
    envVars:
      - key: DB_PATH
        value: /data/moa.db
      - key: CONFIG_PATH
        value: /data/config.json
      - key: GROQ_API_KEY
        sync: false # Set in dashboard
    disk:
      name: moa-data
      mountPath: /data
      sizeGB: 1

  # --- Frontend ---
  - type: web
    name: moa-frontend
    env: static
    buildCommand: cd frontend && pnpm install && pnpm build
    staticPublishPath: frontend/dist
    envVars:
      - key: VITE_API_URL
        fromService:
          type: web
          name: moa-backend
          property: host
```

---

## Important Notes
- **Cold Starts:** If using the Free tier, the backend will spin down after inactivity, causing a ~30s delay on the first request.
- **SQLite Locking:** Render's persistent disks do not support multiple instances. Ensure you only have **1 instance** of the backend running.
- **Port:** Render automatically sets the `$PORT` environment variable; the start command above uses it correctly.
