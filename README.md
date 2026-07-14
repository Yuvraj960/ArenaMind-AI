# ArenaMind AI

**Generative AI Operating System for FIFA World Cup 2026 Stadiums**

Serves four stakeholders — Fans, Volunteers, Operations, and Emergency/Security — through a multi-agent LLM platform. The system runs fully offline (no Docker required) with simulated crowd, transit, and weather data; it upgrades seamlessly when Postgres, Qdrant, and an Anthropic API key are provided.

---

## Demo beats

| # | Beat | How it works |
|---|---|---|
| 1 | 🇪🇸 Spanish fan navigation | Fan asks "¿Dónde está la Gate A?" → routed to NavigationAgent → avoids congested Gate B (85%) → returns Gate C route |
| 2 | 📊 Crowd surge alert | `/stadium/simulate/event` with `affects_gate=gate_b& multiplier=3.0` raises density → ops dashboard reflects it |
| 3 | 🚑 Medical emergency | Incident at Section 103 → EmergencyAgent returns 3 nearest exits + medical + EN/ES/FR/AR announcements |
| 4 | 🌧️ Rain-driven transit | Metro Line 2 delay in simulator triggers crowd narrative update |
| 5 | 🏁 Post-match summary | `/crowd/heatmap` includes GenAI narrative generated from simulator state |

---

## Quick start (offline, no Docker)

### Frontend

```bash
cd arenamind/frontend
npm install
npm run dev
# → opens at http://localhost:3000
```

### Backend

```bash
cd arenamind/backend
pip install -r requirements.txt   # or pip install fastapi uvicorn pytest pytest-asyncio httpx pydantic pydantic-settings scikit-learn
uvicorn app.main:app --reload --port 8000
# → API at http://localhost:8000
#    No API key needed — MockLLMClient activates automatically
#    No Postgres — DB init is skipped with a non-fatal warning
```

**Health check:**
```bash
curl http://localhost:8000/api/v1/
# {"success": true, ...}
```

**Run tests:**
```bash
cd arenamind/backend
python -m pytest tests/ -v
# → 29/29 pass (no Docker, no API key required)
```

---

## Quick start (full stack, with Docker)

```bash
docker compose up   # Postgres, MongoDB, Redis, Qdrant
```

Set environment variables in `arenamind/backend/.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
POSTGRES_PASSWORD=arenamind
```

Then `uvicorn app.main:app` as above — real LLM, real vector DB, real PostgreSQL activate automatically.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)             │
│  / → role select                                      │
│  /fan → Matchday Assistant (chat + gate densities)  │
│  /ops/dashboard → Ops Copilot (gate grid + surge)   │
│  /emergency → Emergency AI (incident → response plan)│
│  /volunteer → Volunteer Copilot (scoped SOP RAG)     │
└──────────────────────────────────────────────────────┘
          HTTP /api/v1/*  ←→  FastAPI gateway
                          │
          ┌───────────────┼──────────────────┐
          ▼               ▼                  ▼
   MasterAgent      NavigationAgent     EmergencyAgent
   (keyword router) (crowd scoring)     (proximity search)
          │               │                  │
   ┌──────┴───────┐      StadiumSimulator   │
   │              │      (seeded: Gate B=85%)│
 KnowledgeAgent  OperationsAgent            │
   │  (TF-IDF RAG) (transit/weather)        │
   └──────────┬──────┘                      │
              ▼                             │
         LocalKBIndex                      │
         (62 chunks, 7 files)              │
         No external deps                 │
```

**Pattern: gather_data → single LLM call → narrative**

Each agent collects real data (simulator, RAG, haversine proximity) in Python, then makes exactly one LLM call for the final narrative. This design works offline (mock LLM) and degrades gracefully — no fragile tool-call loops.

**MockLLMClient** activates when `ANTHROPIC_API_KEY` is absent. All responses include `(mode: mock)` or `(mock mode)` so test output and demo sessions are never silently presented as live model output.

---

## Stakeholders

| Role | Endpoint | Description |
|---|---|---|
| Fan | `POST /api/v1/chat` | Matchday Q&A, multilingual, RAG-backed |
| Operator | `POST /api/v1/operations/query` | Natural-language ops questions |
| Volunteer | `POST /api/v1/chat` (role=volunteer) | Scoped SOP RAG |
| Emergency | `POST /api/v1/emergency/respond` | Full response plan generator |

---

## Key endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/chat` | Fan/volunteer/emergency chat |
| `POST` | `/api/v1/navigation/route` | Crowd-aware navigation |
| `GET` | `/api/v1/crowd/gates` | Gate density list (Gate B = 85%) |
| `GET` | `/api/v1/crowd/heatmap` | Heatmap points + GenAI narrative |
| `POST` | `/api/v1/operations/query` | Ops copilot question |
| `POST` | `/api/v1/emergency/respond` | Emergency response plan |
| `POST` | `/api/v1/stadium/simulate/event` | Trigger dynamic event |
| `GET` | `/api/v1/stadium/weather` | Simulated weather |
| `GET` | `/api/v1/stadium/transit` | Simulated transit |

---

## Knowledge base

62 chunks across 7 files in `arenamind/knowledge_base/`:

| File | Role scope | Languages |
|---|---|---|
| `gates-navigation.md` | fan, volunteer | EN |
| `gates-navigation-es.md` | fan | ES |
| `accessibility.md` | fan, volunteer | EN |
| `amenities.md` | fan | EN |
| `emergency-procedures.md` | fan, volunteer | EN |
| `faqs.md` | fan | EN |
| `volunteer-handbook.md` | volunteer | EN |

RAG uses TF-IDF cosine similarity (no Qdrant required for offline mode). Role scoping filters by `CATEGORY_ROLES` so volunteers see volunteer-specific SOPs.

---

## Backend file structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI entry, lifespan
│   ├── core/
│   │   ├── config.py            # Settings (KNOWLEDGE_BASE_PATH auto-detects Docker vs dev)
│   │   └── llm_client.py        # Anthropic / OpenAI / MockLLMClient
│   ├── agents/
│   │   ├── master_agent.py      # Keyword router
│   │   ├── knowledge_agent.py   # RAG-backed Q&A
│   │   ├── navigation_agent.py  # Crowd-score routing
│   │   ├── operations_agent.py  # Ops copilot
│   │   ├── emergency_agent.py   # Response + proximity search
│   │   ├── crowd_agent.py       # Heatmap + narrative
│   │   └── base_agent.py        # gather_data → LLM → response pattern
│   ├── rag/
│   │   ├── retriever.py         # LocalKnowledgeIndex (TF-IDF, always works)
│   │   └── ingest.py            # Chunking + indexing (stretch: Qdrant)
│   ├── simulators/
│   │   └── stadium_simulator.py # Crowd, weather, transit, Gate B=85%
│   ├── models/schemas.py        # Pydantic models — single source of truth
│   ├── api/v1/
│   │   ├── router.py
│   │   └── endpoints/
│   │       ├── chat.py
│   │       ├── navigation.py    # RouteBuilder converts agent output → Route schema
│   │       ├── crowd.py
│   │       ├── operations.py
│   │       ├── emergency.py
│   │       ├── stadium.py
│   │       └── auth.py
│   └── db/database.py           # Async SQLAlchemy + NullPool (Postgres skipped if unreachable)
├── tests/
│   ├── conftest.py              # KB path setup, TestClient fixture, singleton reset
│   ├── test_agents.py           # 17 tests: routing, agent outputs, simulator, RAG
│   └── test_api.py              # 12 tests: all API endpoints
└── requirements.txt
```

---

## Tech stack

| Layer | Choice | Offline mode |
|---|---|---|
| Frontend | Next.js 14 App Router, TypeScript, Tailwind | — |
| Backend | FastAPI, Python 3.11+, async SQLAlchemy | — |
| AI Gateway | Provider-agnostic LLM (Anthropic → OpenAI → Mock) | Mock with `(mode: mock)` flag |
| RAG | LangChain + Qdrant (stretch) | Local TF-IDF cosine similarity (always works) |
| DB | PostgreSQL (async SQLAlchemy) | Skipped if unreachable |
| Cache | Redis (stretch) | Not used in offline mode |
| Event streaming | Redpanda/Kafka (stretch) | Not used in offline mode |
| Maps | Leaflet + OpenStreetMap | Self-hosted GeoJSON |
| LLM | Claude Sonnet via Anthropic API | MockLLMClient (deterministic, scenario-aware) |

---

## Demo script (5 beats, ~8 minutes)

**Setup:** Start backend (`uvicorn`) and frontend (`npm run dev`). No Docker needed.

```
[Beat 1 — Spanish Fan Navigation]          (~90s)
  Open: http://localhost:3000/fan
  Fan types: "¿Dónde está la Gate A?"
  → routed to navigation agent
  → Gate B at 85% is flagged and avoided
  → response cites Gate C (~20% density)
  → note: English speaker asks "Where can I buy food?" → knowledge agent, sourced answer

[Beat 2 — Ops Sees Crowd Surge]             (~90s)
  Open: http://localhost:3000/ops/dashboard
  Show Gate B at 85%
  Click "🔥 Trigger surge at Gate B"
  → density increases
  → GenAI narrative updates ("Gate B trending high...")

[Beat 3 — Medical Emergency]               (~90s)
  Open: http://localhost:3000/emergency
  Select: Medical, Severity: High
  Details: "Fan collapsed near Section 103"
  → response plan: 3 exits, 3 medical, immediate actions
  → 4-language announcements (EN/ES/FR/AR)

[Beat 4 — Rain-Driven Transit Update]      (~60s)
  Via backend /api/v1/stadium/weather or chat
  Metro Line 2 delay reported by operations agent
  → crowd narrative reflects transit impact

[Beat 5 — Post-Match Summary]              (~60s)
  GET /api/v1/crowd/heatmap
  → "narrative" field contains GenAI crowd summary
  → verify it mentions Gate B
```

---

## Environment variables

```env
# Required for live AI
ANTHROPIC_API_KEY=sk-ant-...      # optional; MockLLM activates if absent

# Required for live DB (optional — skipped gracefully if absent)
DATABASE_URL=postgresql+asyncpg://arenamind:arenamind@localhost:5432/arenamind

# Optional: Qdrant for vector search (local TF-IDF used if absent)
QDRANT_URL=http://localhost:6333

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Project status

| Phase | Status |
|---|---|
| Phase 0 — Backend bootable offline | ✅ 29/29 tests pass |
| Phase 1 — Matchday Assistant core | ✅ |
| Phase 2 — Navigation Agent | ✅ |
| Phase 3 — Crowd Intelligence + Ops Copilot | ✅ |
| Phase 4 — Emergency AI + Volunteer Copilot | ✅ |
| Phase 5 — Next.js Frontend (4 roles) | ✅ Builds clean |
| Phase 6 — Tests + docs + demo script | ✅ README done |

> **Note:** This is a demo/proof-of-concept environment. Simulated data is clearly labeled as simulated. Live CCTV, drone feeds, and real-time CV pipelines are not connected — the stadium simulator provides synthetic data for all such features.