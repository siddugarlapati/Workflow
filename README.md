# Aegis ⚡ — AI-Powered Enterprise Workforce Accountability Platform

**Aegis** is a production-grade, full-stack compliance and task coordination suite that replaces scattered spreadsheets, chat threads, and verbal instructions with a single, verifiable source of truth. It enforces accountability through AI-driven credibility verification, an immutable audit trail, and real-time team intelligence.

---

## 🚀 Quick Start

### Prerequisites

| Dependency | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.13+ | Backend runtime |
| **Node.js** | 20+ | Frontend runtime |
| **Ollama** | Latest | Local AI fallback |
| **Gemini API Key** | — | Primary AI engine (optional) |

### 1. Start the Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --port 8005 --reload
```

### 2. Start the Frontend

```bash
npm install
npm run dev
```

### 3. Open the App

| Service | URL |
|---------|-----|
| **Web App** | [http://localhost:5173](http://localhost:5173) |
| **API Docs** | [http://localhost:8005/docs](http://localhost:8005/docs) (Swagger) |
| **Ollama** | [http://localhost:11434](http://localhost:11434) |

---

## 👤 Demo Credentials

**Manager Account (full access):**
| Field | Value |
|-------|-------|
| Email | `manager@aegis.com` |
| Password | `AegisAdmin2024!` |

**Employee Account (limited access):**
| Field | Value |
|-------|-------|
| Email | `james.smith@aegis.com` |
| Password | `EmployeePass2024!` |

> Quick-login buttons are available on the login page for one-click access.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Shells                        │
│  ┌─────────────────┐  ┌──────────┐  ┌──────────┐       │
│  │  React + Vite   │  │ Capacitor│  │ Capacitor│       │
│  │  Web Dashboard  │  │  Android │  │   iOS    │       │
│  └────────┬────────┘  └────┬─────┘  └────┬─────┘       │
└───────────┼─────────────────┼──────────────┼────────────┘
            │                 │              │
            │       JWT Bearer / HTTP REST                │
            ▼                 ▼              ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Asynchronous Gateway                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │   Auth   │  │   Tasks  │  │   Audit  │  │   AI   │ │
│  │  Router  │  │  Router  │  │  Router  │  │ Router │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
└────────┼──────────────┼────────────┼──────────────┼─────┘
         │              │            │              │
         ▼              ▼            ▼              ▼
┌─────────────────────────────────────────────────────────┐
│             Storage & AI Engine Layer                    │
│  ┌──────────────────┐  ┌────────────────────────────┐   │
│  │   SQLite + WAL   │  │  AI: Gemini → Ollama ↻     │   │
│  │  Immutable Audit │  │  LangChain + LangGraph      │   │
│  └──────────────────┘  └────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Frontend — React + Vite (`src/`)
- **React 19** + **Vite 8** with **React Router v7**
- **Tailwind CSS v4** with custom Material Design token system
- **Google Fonts**: Inter (body), Geist (headings/labels)
- **Material Symbols** (variable icon font)
- **Role-based routing**: `/manager` and `/employee` dashboards
- **JWT Auth** with secure token management via `AuthContext`
- **Axios** HTTP client with auto-injecting JWT interceptor
- **ReactMarkdown** for AI-generated briefings

### Backend — FastAPI (`backend/`)
| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Routers** | `backend/app/routers/` | API endpoints (auth, tasks, logs, ai, audit, chatbot) |
| **Services** | `backend/app/services/` | Business logic & AI orchestration |
| **Repositories** | `backend/app/repositories/` | SQL data access layer |
| **Models** | `backend/app/models/` | SQLModel table definitions |
| **Schemas** | `backend/app/schemas/` | Pydantic request/response schemas |
| **Core** | `backend/app/core/` | LLM factory, security, document parser |

### Native Mobile — Capacitor (`ios/`, `android/`)
- Capacitor bridges the React app into native iOS (Xcode/Swift) and Android (Gradle/Java)
- `capacitor.config.json` points web directory to `dist/`
- Run `npm run mobile:sync` to build and sync

---

## 🧠 AI Intelligence Layer

Aegis uses a **dual-provider AI architecture** with automatic fallback:

| Provider | Role | Requirement |
|----------|------|-------------|
| **Google Gemini 2.5 Flash** | Primary | `GEMINI_API_KEY` in `.env` |
| **Ollama (llama3.2:3b)** | Auto-fallback | Running `ollama serve` |

If Gemini is **unavailable, quota-exhausted (429), or misconfigured**, the system **silently falls back** to the local Ollama model using LangChain's `.with_fallbacks()` — no errors, no disruption.

### AI Features

| Feature | Implementation | Endpoint |
|---------|---------------|----------|
| **Work Log Verification** | Evaluates employee logs → High/Medium/Low confidence | `POST /api/logs/{task_id}` |
| **Manager Briefing** | Plain-English "Where's my team?" summary | `GET /api/ai/summary` |
| **LangGraph Agent** | Risk analysis → anomaly detection → recommendations | `GET /api/ai/agent-analysis` |
| **Smart Task Triage** | Suggests priority & deadline from description | `POST /api/ai/suggest-priority` |
| **AI Chatbot** | Conversational task management via LangChain | `POST /api/ai/chatbot` |

---

## 🎨 UI Design System

The frontend uses a polished **Material Design 3-inspired** system:

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#004ac6` | Buttons, links, active states |
| `--color-surface` | `#f8f9ff` | Page backgrounds |
| `--color-error` | `#ba1a1a` | Overdue, low confidence |
| `--color-tertiary` | `#943700` | Flagged items, warnings |
| Glass effect | `backdrop-blur-xl` | Cards, navbars, modals |
| Bento grid | 12-column CSS Grid | Dashboard layout |
| Focus ring | `ring-4 ring-[#004ac6]/8` | Interactive elements |

### Key UI Components

- **Login Page** — Premium glass card with gradient orbs, demo quick-login buttons
- **Manager Dashboard** — 4-tab navigation (Home, Tasks, Audit Trail, Settings), AI briefing, task metrics, team capacity bars, workload chart, AI verification detail panel, floating chatbot
- **Employee Dashboard** — Glass sidebar, search, task cards with selection, work log submission form, AI verification history
- **Chat Widget** — Floating AI supervisor with markdown responses
- **Modals** — Animated task assignment form with backdrop blur

---

## 🔐 Authentication & Security

- **JWT (HS256)** tokens with 24-hour expiry
- **Role-Based Access Control (RBAC)**: Manager vs Employee routes
- Tokens stored in `localStorage` as `wf_token`
- Protected routes enforce authentication + role check
- Immutable audit trail for every operation

---

## 🗄️ Database

- **SQLite** with **WAL mode** for high-concurrency reads
- **SQLModel** ORM (SQLAlchemy + Pydantic)
- **Tables**: `User`, `Task`, `WorkLog`, `AuditLog`
- Background daemon auto-marks overdue tasks on boot

---

## 📊 Simulation Suite

```bash
cd backend
uv run python scripts/simulate_user.py
```

This simulates the full lifecycle: register manager → onboard 15 employees across 8 departments → assign 15 tasks → submit work logs with AI verification → update statuses → pull AI briefing → LangGraph analysis → 140+ audit trail entries.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite 8, Tailwind CSS v4, React Router v7, Axios |
| **Backend** | Python 3.13, FastAPI, SQLModel, LangChain, LangGraph |
| **AI** | Google Gemini 2.5 Flash, Ollama (llama3.2:3b) |
| **Mobile** | Capacitor 8 (iOS + Android) |
| **Database** | SQLite + WAL mode |
| **Auth** | JWT (HS256), bcrypt |

---

## 📁 Project Structure

```
├── backend/
│   └── app/
│       ├── routers/      # API endpoints
│       ├── services/     # Business logic
│       ├── repositories/ # Data access
│       ├── models/       # SQL tables
│       ├── schemas/      # Pydantic schemas
│       ├── core/         # LLM factory, security
│       ├── middleware/   # Auth middleware
│       ├── main.py       # App entrypoint
│       ├── config.py     # Settings
│       └── database.py   # DB engine
├── src/                  # React frontend
│   ├── pages/            # Dashboard pages
│   ├── components/       # Shared components
│   ├── context/          # Auth context
│   ├── api/              # API client
│   └── index.css         # Design system
├── ios/                  # Capacitor iOS shell
├── android/              # Capacitor Android shell
├── scripts/              # Demo & simulation
└── stitch_reference/     # Design mockups
```
