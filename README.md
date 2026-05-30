# Aegis ⚡ — AI-Powered Enterprise Workforce Accountability Platform

**Aegis** is a full-stack, production-grade compliance and task coordination suite that replaces scattered spreadsheets, chat threads, and verbal instructions with a single, verifiable source of truth. The platform enforces accountability through AI-driven credibility verification, an immutable audit trail, real-time team intelligence, and autonomous browser-based proof auditing.

---

## 🚀 Quick Start

### Prerequisites

| Dependency | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.12+ | Backend runtime |
| **Node.js** | 20+ | Frontend runtime |
| **Ollama** | Latest | Local AI inference (fallback) |
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
| Email | `manager@demo.com` |
| Password | `password123` |

**Employee Account (limited access):**
| Field | Value |
|-------|-------|
| Email | `employee1@demo.com` |
| Password | `password123` |

> Quick-login buttons are available on the login page for one-click access.

---

## 🧠 AI Intelligence Layer

Aegis employs a **dual-provider AI architecture** with automatic fallback, ensuring uninterrupted operation regardless of cloud API availability.

| Provider | Role | Requirement |
|----------|------|-------------|
| **Google Gemini 2.5 Flash** | Primary inference engine | `GEMINI_API_KEY` in `.env` |
| **Ollama (llama3.2:3b)** | Automatic local fallback | Running `ollama serve` |

When Gemini is **unavailable, quota-exhausted (429), or misconfigured**, the system **silently falls back** to the local Ollama model via LangChain's `.with_fallbacks()` — zero disruption, zero errors.

### AI Capabilities

| Feature | Implementation | Endpoint |
|---------|---------------|----------|
| **Autonomous Work Log Verification** | Multi-stage AI credibility scoring (High/Medium/Low) | `POST /api/logs/{task_id}` |
| **Manager Team Briefing** | Plain-English "Where's my team?" executive summary | `GET /api/ai/summary` |
| **LangGraph Accountability Agent** | Multi-step risk analysis, anomaly detection, and recommendations | `GET /api/ai/agent-analysis` |
| **Smart Task Triage** | Priority and deadline suggestions from task descriptions | `POST /api/ai/suggest-priority` |
| **AI Chatbot Supervisor** | Conversational task assignment with auto-triage | `POST /api/ai/chatbot` |
| **AI Health Check** | Real-time provider status monitoring | `GET /api/ai/health` |

---

## 🔍 Cognitive Verification Engine

The heart of Aegis is its **Autonomous Cognitive Verifier** — a multi-stage AI auditing pipeline that goes far beyond simple LLM prompting. It combines three advanced verification paradigms:

```mermaid
flowchart TB
    subgraph Input["📤 Submission Layer"]
        A["Employee submits work log"] --> A1["Text log entry"]
        A -->        A2["File attachment<br/>(PDF, DOCX, XLSX, PNG)"]
        A2 -->        A3["Document Parser<br/>Extracts structured text"]
    end

    subgraph Classification["🔀 Dynamic Classification"]
        B["Task-Adaptive<br/>Classifier"] --> C1["🌐 Web Development"]
        B --> C2["📞 Lead Generation"]
        B --> C3["📊 Document / Spreadsheet"]
        B --> C4["✅ General Compliance"]
    end

    subgraph Audit["🔍 Proof Auditing"]
        D1{"URL detected?"} -->|Yes|        E1["Playwright E2E Browser<br/>Headless Chromium crawl"]
        D1 -->|No| D2
        D2{"Image / scanned\nPDF detected?"} -->|Yes|        E2["Gemini Vision API<br/>Live cognitive analysis"]
        D2 -->|No| F["Text-only evaluation"]
        E1 --> F
        E2 --> F
    end

    subgraph Alignment["⚖️ Outcome-Prediction Alignment"]
        G["Compare expected criteria\nvs. submitted proof"]
        G --> H1{"Alignment\nscore > 0.2?"}
        H1 -->|No| I["🚨 Bluff flagged\nLow confidence"]
        H1 -->|Yes| J["✓ Proceed to LLM"]
    end

    subgraph LLM["🧠 LLM Verification"]
        K["Gemini 2.5 Flash"] --> L["Confidence<br/>scoring"]
        M["Ollama fallback<br/>(llama3.2:3b)"] --> L
        L --> N["High /<br/>Medium / Low"]
    end

    subgraph Output["📋 Output & Audit"]
        O["Pedagogical feedback<br/>Self-corrective guidance"]
        P["Immutable audit trail"]
        Q["RAG index<br/>Semantic search"]
    end

    Input --> Classification
    Classification --> Audit
    Audit --> Alignment
    Alignment --> LLM
    LLM --> Output

    style A fill:#1e3a5f,color:#fff
    style I fill:#ba1a1a,color:#fff
    style N fill:#004ac6,color:#fff
    style E1 fill:#2d4a3e,color:#fff
    style E2 fill:#2d4a3e,color:#fff
```

### 1. Dynamic Task-Adaptive Classification

Rather than applying a one-size-fits-all verification strategy, the engine **dynamically classifies each task** into one of four categories — Web Development, Lead Generation & Calls, Document & Spreadsheet Analysis, or General Compliance — and applies **tailored verification rules** specific to each category. This adaptive classification ensures that a web deployment check uses different criteria than a spreadsheet audit or a client outreach verification, maximizing relevance and accuracy.

### 2. Outcome-Prediction Alignment

The system evaluates submitted proof by **comparing expected target outcomes against actual proof representations**. It analyzes linguistic specificity, quantitative detail, and structural completeness of submissions to detect evasive patterns, generic responses, and low-effort entries. This alignment check surfaces discrepancies between what was assigned and what was delivered, flagging mismatches with precision.

### 3. Autonomous Browser-Based Proof Auditing

For web development tasks, Aegis deploys **Playwright-powered headless browser automation** to:
- Crawl submitted deployment URLs in real time
- Extract page titles, content, and form elements
- Analyze for required features (signup forms, input fields, etc.)
- Detect placeholder domains and non-functional deployments
- Capture JavaScript console anomalies for deeper investigation

### 4. Visual Proof Validation

When image screenshots or scanned PDFs are submitted as proof, the system **base64-encodes the visual data and routes it through Gemini's Vision API** for live cognitive analysis. This catches attempts to submit empty screenshots, unrelated images, or fabricated visual proof — a layer of verification impossible with text-only analysis.

### 5. Pedagogical Feedback Generation

When a bluff or low-confidence submission is detected, the engine generates **structured, actionable feedback** explaining exactly what was flagged and why, along with self-corrective guidance. This transforms verification from a gatekeeping function into a coaching mechanism that helps employees improve the quality of their submissions.

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
            │       JWT Bearer / HTTP REST                 │
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
| **Core** | `backend/app/core/` | LLM factory, security, document parser, cognitive verifier |

### Native Mobile — Capacitor (`ios/`, `android/`)
- Capacitor bridges the React app into native iOS (Xcode/Swift) and Android (Gradle/Java)
- `capacitor.config.json` points web directory to `dist/`
- Run `npm run mobile:sync` to build and sync

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
- **Immutable append-only audit trail** for every operation — never deleted, tamper-resistant

---

## 🗄️ Database

- **SQLite** with **WAL mode** for high-concurrency reads
- **SQLModel** ORM (SQLAlchemy + Pydantic)
- **Tables**: `User`, `Task`, `WorkLog`, `AuditLog`
- Background daemon auto-marks overdue tasks on boot

---

## 📄 Document Intelligence

Aegis supports **multi-format document parsing** for submitted proof files:

| Format | Parser | Capability |
|--------|--------|------------|
| PDF | PyPDF2 / Gemini Vision API | Text extraction + scanned document analysis |
| Word (.docx) | python-docx | Paragraph-level extraction |
| Excel (.xlsx) | openpyxl | Cell-by-cell row extraction from all sheets |
| Images (PNG, JPG, WEBP) | EasyOCR / Tesseract / Gemini Vision | OCR text extraction + base64 Vision analysis |
| Plaintext / CSV | UTF-8 / Latin-1 decoding | Direct text ingestion |

Scanned PDFs and screenshot images are automatically base64-encoded and routed to **Gemini's Vision API** for live cognitive auditing, closing the "scanned vectorless document" loophole.

---

## 🤖 LangGraph Accountability Agent

Aegis includes a **multi-step AI agent** built on LangGraph that orchestrates:

1. **Risk Analysis** — Identifies overdue tasks, high-priority items, and tasks with zero work log submissions
2. **Anomaly Detection** — Flags employees with recurring low-confidence submissions and pattern-based concerns
3. **Recommendation Generation** — Produces 3 specific, actionable recommendations for the manager

The agent runs as a stateful graph (analyse → flag → recommend) using Gemini for each step, with automatic Ollama fallback at every stage.

---

## 📊 Simulation Suite

```bash
cd backend

# Quick demo: seed database with sample accounts and tasks
uv run python scripts/seed.py

# Full lifecycle simulation: onboard → assign tasks → submit logs → AI verify → audit
uv run python scripts/simulate_user.py

# E2E simulation with bluff detection and Playwright browser auditing
uv run python scripts/simulate_company_workflow.py

# E2E test suite: register, login, task CRUD, log submission, AI verification
uv run python scripts/e2e_test.py

# Cognitive agent test: blank document uploads, bluff URLs, Gemini Vision analysis
uv run python scripts/test_cognitive_agent.py
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite 8, Tailwind CSS v4, React Router v7, Axios |
| **Backend** | Python 3.12, FastAPI, SQLModel, LangChain, LangGraph |
| **AI** | Google Gemini 2.5 Flash, Ollama (llama3.2:3b) |
| **Browser Automation** | Playwright (headless Chromium) |
| **Mobile** | Capacitor 8 (iOS + Android) |
| **Database** | SQLite + WAL mode (optional PostgreSQL via pgvector) |
| **Auth** | JWT (HS256), bcrypt |
| **Document Parsing** | PyPDF2, python-docx, openpyxl, EasyOCR, Tesseract |

---

## 🐳 Docker Support

```bash
docker compose up -d
```

Starts optional PostgreSQL (pgvector) and Ollama containers for production deployments.

---

## 📁 Project Structure

```
├── backend/
│   └── app/
│       ├── routers/        # API endpoints
│       ├── services/       # Business logic & AI orchestration
│       ├── repositories/   # Data access layer
│       ├── models/         # SQL table definitions
│       ├── schemas/        # Pydantic schemas
│       ├── core/           # LLM factory, security, document parser, cognitive verifier
│       ├── middleware/     # Auth middleware
│       ├── main.py         # App entrypoint
│       ├── config.py       # Settings
│       └── database.py     # DB engine
├── src/                    # React frontend
│   ├── pages/              # Dashboard pages
│   ├── components/         # Shared components
│   ├── context/            # Auth context
│   ├── api/                # API client
│   └── index.css           # Design system
├── ios/                    # Capacitor iOS shell
├── android/                # Capacitor Android shell
├── scripts/                # Demo, simulation & E2E tests
├── stitch_reference/       # Design mockups
└── docker-compose.yml      # PostgreSQL + Ollama containers
```

---

## 🔧 Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Required
JWT_SECRET=your-secure-secret-here

# Optional (falls back to local Ollama if not set)
GEMINI_API_KEY=your-gemini-api-key
```
