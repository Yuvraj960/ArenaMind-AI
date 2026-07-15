# Deploying ArenaMind AI to Render

Deploy step by step. Services must be created in this order — later services depend on earlier ones.

---

## TL;DR — Deploy order

```
1. Create PostgreSQL (Render dashboard)
2. Create Redis (Render dashboard)
3. Deploy backend (render.yaml — paste DB + Redis URLs)
4. Deploy frontend (render.yaml — paste backend URL)

Total: ~20 minutes. Cost: $0 on free tier.
```

---

## Step 1 — Create PostgreSQL

1. Render Dashboard → **New** → **PostgreSQL**
2. Settings:
   - **Name:** `arenamind-db`
   - **Region:** Oregon
   - **Plan:** Starter (Free)
3. Click **Create Database**
4. Wait for status → **Available**
5. Go to **Connections** panel, scroll to **Internal Connection URL**
6. Copy the full URL — it looks like `postgres://arenamind:ABC123@.../arenamind`
   - Store this — you paste it into Step 3

---

## Step 2 — Create Redis

1. Render Dashboard → **New** → **Redis**
2. Settings:
   - **Name:** `arenamind-redis`
   - **Region:** Oregon
   - **Plan:** Starter (Free)
3. Click **Create Redis**
4. Wait for **Available** → copy the **Connection URL**

---

## Step 3 — Deploy the backend

### Option A — Direct dashboard deploy (easiest)

1. Render Dashboard → **New** → **Web Service**
2. Connect your GitHub repo — select the `arenamind` repo
3. Configure:

   | Field | Value |
   |---|---|
   | Name | `arenamind-backend` |
   | Region | Oregon |
   | Branch | `main` |
   | Runtime | Docker |
   | Dockerfile Path | `backend/Dockerfile` |
   | Plan | Free |

4. **Environment variables** — add these:

   | Key | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | ⚠️ Click **Secret** → paste from console.anthropic.com |
   | `ENVIRONMENT` | `production` |
   | `DATABASE_URL` | Paste the Internal URL from Step 1 |
   | `REDIS_URL` | Paste the Connection URL from Step 2 |
   | `KNOWLEDGE_BASE_PATH` | `/app/knowledge_base` |
   | `SECRET_KEY` | Click **Generate** |
   | `CORS_ORIGINS` | `["https://arenamind-frontend.onrender.com","http://localhost:3000"]` |
   | `QDRANT_URL` | (leave empty) |

5. **Health Check Path:** `/api/v1/`
6. Click **Create Web Service**
7. Wait ~4 min for build → verify logs say `[ArenaMind] booted in production mode`

### Option B — Via render.yaml

If using the included `render.yaml`:

1. Push `render.yaml` to GitHub in the repo root (`/arenamind/`)
2. Render Dashboard → **Blueprints** → **Create Blueprint Instance**
3. Select the repo — it will read `render.yaml`
4. For `DATABASE_URL` and `REDIS_URL`: since PostgreSQL/Redis aren't in the same `render.yaml`, set them manually in the service environment variables after the Blueprint deploys

---

## Step 4 — Update CORS on backend

After frontend URL is known (Step 5), update backend:

1. `arenamind-backend` → **Environment** tab
2. Edit `CORS_ORIGINS`:
   ```
   ["https://arenamind-frontend.onrender.com","http://localhost:3000"]
   ```
3. **Redeploy** → Deploy → Manual Deploy → Deploy latest commit

---

## Step 5 — Deploy the frontend

1. Render Dashboard → **New** → **Web Service**
2. Connect the same GitHub repo
3. Configure:

   | Field | Value |
   |---|---|
   | Name | `arenamind-frontend` |
   | Region | Oregon |
   | Runtime | Docker |
   | Dockerfile Path | `frontend/Dockerfile` |
   | Plan | Free |

4. **Environment variables:**

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://arenamind-backend.onrender.com/api/v1` |
   | `NODE_ENV` | `production` |
   | `NEXT_TELEMETRY_DISABLED` | `1` |

5. Click **Create Web Service**
6. Wait ~3 min → open `https://arenamind-frontend.onrender.com`

---

## Step 6 — Initialize the database (first run only)

1. **arenamind-backend** → **Shell**
2. Run:
   ```bash
   python -c "
   import asyncio
   from app.db.database import init_db
   asyncio.run(init_db())
   print('DB schema created')
   "
   ```

---

## Verifying the deployment

```bash
# Backend health
curl https://arenamind-backend.onrender.com/api/v1/

# Chat (real AI if ANTHROPIC_API_KEY is set, mock otherwise)
curl -s -X POST https://arenamind-backend.onrender.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Where is the accessible entrance?","language":"en","role":"fan","session_id":"test"}' \
  | python -m json.tool | grep -E '"response"|"agent_used"|"llm_mode"'

# Frontend
open https://arenamind-frontend.onrender.com
```

---

## After code changes

```bash
git push main
# → GitHub webhook triggers auto-deploy on both services
```

To manually redeploy:
`arenamind-backend` → **Deploy** → Deploy latest commit (rebuilds + restarts)

---

## Production URLs (replace with yours)

| Service | URL |
|---|---|
| Frontend | `https://arenamind-frontend.onrender.com` |
| Backend API | `https://arenamind-backend.onrender.com` |
| API Health | `https://arenamind-backend.onrender.com/api/v1/` |
| Swagger docs | `https://arenamind-backend.onrender.com/docs` |

---

## Common issues

| Problem | Fix |
|---|---|
| `llm_mode: mock` in every response | Set `ANTHROPIC_API_KEY` as a Render Secret (not plain text) |
| Frontend 502 | Backend is asleep — hit the backend URL once to wake it |
| CORS error in browser | Update `CORS_ORIGINS` on backend to include the frontend URL, then redeploy |
| `KNOWLEDGE_BASE_PATH` wrong | Set to `/app/knowledge_base` — files are copied by the Dockerfile |
| DB init fails | Check `DATABASE_URL` is the **Internal** connection URL, not the External one |
| Frontend shows wrong backend | Rebuild frontend after setting `NEXT_PUBLIC_API_URL` (Next.js bakes it at build time) |

---

## Keeping services awake (free tier)

Render's free tier sleeps services after 15 min of no traffic. For a demo, either:
- **Paid plan** (~$7/month/service) — services never sleep
- **Uptime monitor** — a free service like Pingram or HetrixTools that pings `/api/v1/` every 9 minutes keeps both services warm

Example cron for a free uptime monitor targeting both services:
```
*/9 * * * * curl -s -o /dev/null https://arenamind-backend.onrender.com/api/v1/
*/9 * * * * curl -s -o /dev/null https://arenamind-frontend.onrender.com/
```