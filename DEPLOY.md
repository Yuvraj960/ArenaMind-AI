# Deploying ArenaMind AI

Two paths. **Option A** is simpler and fully self-contained on one VPS. **Option B** separates concerns across specialist hosted platforms.

---

## Option A — Single VPS with Docker Compose

Best for: self-hosting, hackathon demos, personal projects. One server, ~$6–20/month.

### 1. Provision a VPS
Ubuntu 22.04 on any cloud (DigitalOcean Droplet, Hetzner, Linode, AWS EC2).

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and log back in, then:
docker --version
```

### 2. Upload the project
```bash
# From your local machine
rsync -avz --exclude='.git/' --exclude='.next/' --exclude='node_modules/' \
  ./arenamind/ root@YOUR_VPS_IP:/opt/arenamind/
```

### 3. Create `.env` at `/opt/arenamind/.env`
```env
# AI — get a key from console.anthropic.com (free tier works)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Database
POSTGRES_PASSWORD=change-this-to-a-strong-password

# Security
SECRET_KEY=generate-a-64-char-random-string-here
ENVIRONMENT=production
CORS_ORIGINS=["http://your-vps-ip:3000"]  # add your domain later

# Optional: if using Qdrant for vector search
# QDRANT_URL=http://qdrant:6333
```

### 4. Start everything
```bash
cd /opt/arenamind
docker compose up -d --build

# Watch logs
docker compose logs -f backend

# Seed the database (first run only)
docker compose exec backend python -c "
import asyncio
from app.db.database import init_db
asyncio.run(init_db())
print('DB initialized')
"
```

### 5. Verify
```bash
curl http://localhost:8000/api/v1/
# → {"success": true, ...}

curl http://localhost:3000
# → ArenaMind landing page
```

### 6. Bind to a domain (optional)
```bash
# Install Caddy for automatic HTTPS
sudo apt install -y caddy

# /etc/Caddyfile:
arenamind.your-domain.com {
    reverse_proxy localhost:3000
    handle_path /api/* {
        reverse_proxy localhost:8000
    }
}

sudo systemctl reload caddy
```

Update `CORS_ORIGINS` in `.env` to include your domain, then `docker compose restart backend`.

---

## Option B — Cloud-native split (recommended for production)

Separate concerns: managed database, stateless compute, CDN. Costs ~$15–40/month but zero maintenance.

### Backend → Railway

1. Create a new Railway project at [railway.app](https://railway.app)
2. Add a **PostgreSQL** plugin → copy the `DATABASE_URL` Railway gives you
3. Add a **Qdrant** plugin (or use Railway's one-click Qdrant)
4. Connect your GitHub repo and set the root to `arenamind/backend`
5. Add environment variables:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   SECRET_KEY=<random-64-chars>
   ENVIRONMENT=production
   DATABASE_URL=<from step 2>
   QDRANT_URL=<from step 3>
   CORS_ORIGINS=["https://your-frontend.vercel.app"]
   KNOWLEDGE_BASE_PATH=/app/knowledge_base
   ```
6. Railway auto-detects the Dockerfile and deploys on push

**Health check path:** `/api/v1/` — Railway will ping this to confirm the service is healthy.

**Start command (Railway will read from Dockerfile):**
```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend → Vercel

1. Create a new Vercel project at [vercel.com](https://vercel.com)
2. Connect the `arenamind/frontend` directory (or GitHub repo)
3. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app/api/v1
   ```
4. Deploy — Vercel auto-detects Next.js 14

**Or — self-host the frontend:**
```bash
cd arenamind/frontend
docker build -t arenamind-frontend .
docker run -d -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://your-railway-app.up.railway.tech/api/v1 \
  arenamind-frontend
```

---

## Environment variables reference

| Variable | Required | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | For live AI | Free tier at console.anthropic.com |
| `OPENAI_API_KEY` | Alt to Anthropic | Used if ANTHROPIC is absent |
| `DATABASE_URL` | For live DB | Auto-set by Railway/Docker Compose |
| `KNOWLEDGE_BASE_PATH` | For live RAG | Auto-detects inside Docker (`/app/knowledge_base`) |
| `QDRANT_URL` | For vector RAG | Falls back to local TF-IDF if absent |
| `SECRET_KEY` | For auth | Generate: `python -c "import secrets; print(secrets.token_hex(64))"` |
| `CORS_ORIGINS` | For browser access | Array of allowed origins |
| `ENVIRONMENT` | `production` | Enables strict auth; dev mode is lenient |

---

## How graceful degradation works in production

ArenaMind is designed to **work partially when services fail**:

| Service | What fails without it | What still works |
|---|---|---|
| Anthropic API key | `POST /chat` gets mock responses | All other endpoints unaffected |
| PostgreSQL | Chat history not persisted | Everything else still responds |
| Qdrant | Vector search skipped | Local TF-IDF RAG continues |
| Redis | Sessions are stateless | All features work |
| Redpanda/Kafka | Event streaming skipped | No real-time updates (polling still works) |

The `MockLLMClient` response text always includes `(mock mode)` or `(mode: mock)` so you can tell at a glance whether you're using real AI or the fallback.

---

## Production Nginx config (when not using Caddy)

If you run the frontend+backend behind nginx on the same VPS:

```nginx
# /etc/nginx/sites-available/arenamind
server {
    listen 80;
    server_name arenamind.your-domain.com;

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
}
```

---

## Health checks

```bash
# Backend health (from anywhere)
curl https://your-backend.com/api/v1/

# Docker container status
docker compose ps

# Watch for crash loops
docker compose logs --tail=50 backend
```

---

## Updating after code changes

```bash
# Option A (VPS)
cd /opt/arenamind
git pull   # or rsync again
docker compose build backend frontend
docker compose up -d

# Option B (Railway/Vercel)
# Push to GitHub — Railway/Vercel rebuild automatically
```