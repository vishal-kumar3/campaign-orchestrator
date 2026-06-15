# Campaign Orchestrator

Campaign Orchestrator is an AI-powered marketing platform that runs the full campaign lifecycle in one place: brand research, platform-specific content generation, scheduling, human approval, and publishing. Instead of juggling separate tools for competitor analysis, copywriting, scheduling, and analytics, a marketing team works from a single brief and watches specialized agents handle each step.

The system is built around LangGraph agent orchestration. A supervisor coordinates Research, Content, Scheduler, Image Prompt, Publisher, and Analytics agents. Brand guidelines live in a knowledge base backed by RAG retrieval, so generated copy stays on-voice rather than drifting into generic AI tone. Nothing publishes without explicit approval—the workflow pauses at a human-in-the-loop checkpoint before the Publisher agent runs.

---

## Features

**Workspace and campaign management**

Organize work into workspaces. Each campaign carries a title, objective, target audience, region, and target platforms (Twitter, LinkedIn, email, blog). Campaigns move through a status lifecycle: draft → researching → generating → approval pending → completed.

**Brand voice knowledge bases**

Upload brand guideline PDFs to a knowledge base scoped to a workspace or a specific campaign. Documents are extracted, chunked, embedded with Google Gemini, and stored in PostgreSQL with pgvector. Semantic search returns the most relevant brand-voice chunks at generation time.

**REST API with Clerk authentication**

All API routes except health checks require a valid Clerk JWT. Workspaces are scoped to the authenticated user. The frontend attaches Bearer tokens automatically on every request.

**Campaign content management**

Create and edit platform-specific content pieces per campaign. Each piece tracks platform, title, body, variant, and approval status (draft, approved, rejected).

**Multi-agent pipeline**

LangGraph coordinates the campaign workflow:

| Agent | Role |
|---|---|
| Research | Crawls competitor URLs and searches the web for audience sentiment and market gaps |
| Content | Generates platform-optimized copy grounded in brand-voice RAG context |
| Scheduler | Recommends posting times from historical engagement data |
| Image Prompt | Produces DALL-E prompts aligned with campaign content |
| Publisher | Posts approved content to Twitter, LinkedIn, and Mailchimp |
| Analytics | Polls engagement metrics and feeds learnings back into future campaigns |

**Real-time agent streaming**

During campaign execution, agent reasoning is pushed over Server-Sent Events so the dashboard shows live progress—what each agent found, decided, and produced—instead of a generic loading spinner.

**Human approval workflow**

The graph interrupts before publishing. Reviewers see all generated content, edit inline, and approve or reject per platform. Only approved pieces reach the Publisher agent.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js (App Router)                                       │
│  Dashboard · Campaign builder · Approval UI · SSE client    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS / SSE
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI                                                    │
│  /workspaces · /campaigns · /knowledge-bases · /documents   │
└──────────┬─────────────────────────────┬────────────────────┘
           │                             │
┌──────────▼──────────┐       ┌──────────▼──────────┐
│  LangGraph agents   │       │  PostgreSQL         │
│  (agent package)    │       │  + pgvector         │
└──────────┬──────────┘       └─────────────────────┘
           │
┌──────────▼──────────────────────────────────────────┐
│  External APIs                                      │
│  Google Gemini · Tavily · Twitter · LinkedIn · etc. │
└─────────────────────────────────────────────────────┘
```

**Stack**

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS 4, TanStack Query, Clerk |
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic Settings |
| Agents | LangGraph, LangChain, LangSmith tracing |
| Database | PostgreSQL 16 with pgvector extension |
| Embeddings | Google Gemini (`gemini-embedding-001`, 1536 dimensions) |
| LLM | Google Gemini (`gemini-2.0-flash`) |
| Auth | Clerk (JWT verification on backend, middleware on frontend) |
| Containers | Docker Compose |

**Design choices**

- **pgvector over a separate vector database** — embeddings live alongside relational data in Postgres, filtered by knowledge base at query time.
- **Local filesystem storage for PDFs** — uploads are stored under `backend/data/uploads/` with a storage abstraction that can swap to Cloudflare R2 later without changing ingestion logic.
- **In-process agent execution** — the backend imports the `agent` package and runs LangGraph workflows via FastAPI background tasks, keeping the deployment surface small.

---

## Folder structure

```
campaign_orchestrator/
├── frontend/                  # Next.js dashboard
│   ├── app/                   # App Router pages (auth, dashboard, workspace routes)
│   ├── components/            # UI components and page-level views
│   ├── hooks/                 # React hooks (API client)
│   └── lib/                   # API client, types, Zod schemas
│
├── backend/                   # FastAPI API server
│   ├── alembic/               # Database migrations
│   ├── app/
│   │   ├── api/routes/        # REST endpoints
│   │   ├── core/              # Settings and configuration
│   │   ├── db/
│   │   │   ├── models/        # SQLAlchemy ORM models
│   │   │   └── queries/       # Data access helpers
│   │   ├── schemas/           # Pydantic request/response models
│   │   └── services/          # RAG pipeline, embeddings, file storage
│   └── main.py                # FastAPI app entry point
│
├── agent/                     # LangGraph agent orchestration
│   ├── rag_client.py          # HTTP client for backend RAG retrieval
│   └── main.py                # Agent service entry point
│
├── docker-compose.yml         # Local dev stack (frontend, backend, agent, postgres)
└── plan.md                    # Full product specification and phased roadmap
```

---

## Setup

### Prerequisites

- Docker and Docker Compose
- [Clerk](https://clerk.com) account (publishable + secret keys)
- [Google AI Studio](https://aistudio.google.com) API key for Gemini embeddings

Optional for the full agent pipeline:

- [Tavily](https://tavily.com) API key (research agent)
- [LangSmith](https://smith.langchain.com) API key (agent tracing)
- Twitter / LinkedIn / Mailchimp API credentials (publishing)

### 1. Clone and configure environment

```bash
git clone <repository-url>
cd campaign_orchestrator
```

Copy the example env files and fill in your keys:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Environment variables

**`backend/.env`**

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/campaign_ai
CLERK_SECRET_KEY=sk_test_...

GOOGLE_API_KEY=...
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSIONS=1536
GEMINI_CHAT_MODEL=gemini-2.0-flash

UPLOAD_DIR=./data/uploads
MAX_UPLOAD_BYTES=20971520
```

**`frontend/.env`**

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

When running via Docker Compose, `DATABASE_URL` and `UPLOAD_DIR` are overridden in `docker-compose.yml` to point at the containerized Postgres instance and the shared upload volume.

### 3. Start with Docker Compose

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### 4. Run database migrations

With Postgres running (via Compose or locally):

```bash
cd backend
uv sync
uv run alembic upgrade head
```

This enables the pgvector extension and creates all tables: workspaces, campaigns, knowledge bases, documents, document chunks, campaign contents, agent runs, agent logs, workflow threads, and research snapshots.

### 5. Local development without Docker

**Backend**

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run fastapi dev main.py --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd frontend
bun install
bun run dev
```

**Agent service**

```bash
cd agent
uv sync
uv run python main.py
```

Postgres must be reachable at the `DATABASE_URL` in your backend `.env`. The easiest path is to run only the database via Compose:

```bash
docker compose up postgres -d
```

---

## Usage

1. Sign in at http://localhost:3000 (Clerk handles registration and login).
2. Create a workspace from the dashboard.
3. Add a knowledge base and upload a brand guidelines PDF. Processing runs automatically—wait for the document status to reach `indexed`.
4. Create a campaign with an objective, audience, and target platforms.
5. Link the campaign to an indexed knowledge base and run the agent workflow to generate research and platform-specific content.
6. Review generated content in the approval view, edit as needed, and approve pieces for publishing.

---

## API overview

All routes are prefixed with `/api/v1` and require a Bearer token unless noted.

| Method | Path | Description |
|---|---|---|
| GET | `/health/` | Health check (no auth) |
| CRUD | `/workspaces/` | Workspace management |
| CRUD | `/workspaces/{ws}/campaigns/` | Campaign management |
| CRUD | `/workspaces/{ws}/knowledge-bases/` | Knowledge base management |
| POST | `/workspaces/{ws}/knowledge-bases/{kb}/documents/upload` | Upload brand PDF |
| POST | `/workspaces/{ws}/knowledge-bases/{kb}/documents/{id}/process` | Trigger PDF ingestion |
| GET | `/workspaces/{ws}/knowledge-bases/{kb}/retrieve?q=...` | Semantic chunk retrieval |
| CRUD | `/workspaces/{ws}/campaigns/{id}/contents/` | Campaign content pieces |

Interactive API documentation is available at `/docs` when the backend is running.

---

## License

Private project. All rights reserved.
