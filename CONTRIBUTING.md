# Contributing to KawTeam

Thank you for your interest in contributing to KawTeam! This guide will help you get set up and start contributing.

## Getting Started

### Prerequisites

- **Node.js** (v18+ recommended) and npm
- **Python 3.12+** with pip
- A configured Supabase instance (see [Integration Status](docs/INTEGRATION_STATUS.md))

### Local Development Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/shazwanclw/KawTeam.git
   cd KawTeam
   ```

2. **Set up the backend** (FastAPI + Python):

   ```bash
   cd apps/api
   python -m venv .venv
   # Windows
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   # macOS / Linux
   .venv/bin/pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Set up the frontend** (Next.js):

   ```bash
   cd apps/web
   npm ci
   cp .env.example .env.local
   ```

4. Fill in your environment variables following the integration guide.

## Project Structure

```
KawTeam/
├── apps/
│   ├── api/          # FastAPI backend — suppliers, liaison, automation
│   │   ├── src/kawteam/   # Core application modules
│   │   └── tests/         # Backend test suite (pytest)
│   └── web/          # Next.js frontend — chat UI, project dashboard
│       ├── src/components/ # React components
│       ├── src/lib/        # Shared utilities and types
│       └── tests/          # Frontend tests (vitest + Playwright)
├── docs/             # Architecture, specs, demo guides
├── scripts/          # Helper scripts (Supabase, shadcn)
├── supabase/         # Database migrations
└── workbuddy/        # WorkBuddy MCP skill definitions
```

## Running Tests

### Backend

```bash
cd apps/api
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src tests
```

### Frontend

```bash
cd apps/web
npm test
npm run typecheck
npm run lint
```

## Code Style

- **Python**: We use [Ruff](https://docs.astral.sh/ruff/) for linting. Run `ruff check` before committing.
- **TypeScript**: ESLint is configured in the web app. Run `npm run lint` to check.
- Keep functions focused and add docstrings to public API functions.
- Use meaningful variable names over abbreviations.

## Making Changes

1. Create a feature branch from `main`.
2. Make your changes with clear, descriptive commit messages.
3. Run the relevant test suites to ensure nothing is broken.
4. Submit a pull request with a description of what changed and why.

## Hackathon Notes

This project was built for **Dormathon 2026, Track 2** (WorkBuddy agentic solutions). The demo data includes simulated supplier conversations — no real vendors are contacted when loading fixture data.
