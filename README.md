# Mantle Sentinel
Multi-Agent Monitoring System for Intelligent Alert Analysis
---
## Overview
Mantle Sentinel is a hackathon project exploring how multiple specialized AI agents can collaboratively analyze operational alerts and produce explainable consensus decisions.
The system simulates a monitoring environment where alerts are routed to expert agents, evaluated independently, and aggregated into a final recommendation.
---
## Problem
Modern monitoring systems generate excessive alert volume.
Operators experience:
- Alert fatigue
- False positives
- Context switching
- Delayed incident response
Mantle Sentinel explores whether a group of specialized AI agents can improve signal quality through consensus reasoning.
---
## Core Concepts
### Router Agent
Classifies incoming alerts.
Determines which specialist agents should analyze them.
### Specialist Agents
Security Agent
Infrastructure Agent
Operations Agent
Each agent independently evaluates the alert.
### Consensus Engine
Aggregates agent outputs.
Produces:
- Final severity
- Final confidence
- Human-readable explanation
### Memory Engine
Stores prior alert evaluations.
Allows future retrieval and context enrichment.
---
## Architecture
```text
Alert
  ↓
Router Agent
  ↓
Specialist Agents
  ↓
Consensus Engine
  ↓
Memory Engine
  ↓
Dashboard
```
---
## Technology Stack
### Frontend
- Next.js
- TypeScript
- Tailwind
- shadcn/ui
### Backend
- FastAPI
- Python
- Pydantic
### Storage
- SQLite
### Deployment
- Vercel
- Railway
---
## Repository Structure
```text
mantle-sentinel/
frontend/
backend/
docs/
frontend/contracts/
docs/
```
---
## MVP Features
- Alert ingestion
- Schema validation
- Agent routing
- Multi-agent analysis
- Consensus generation
- Memory storage
- Monitoring dashboard
- Public website
---
## Documentation
Architecture:
docs/ARCHITECTURE_FREEZE.md
Implementation:
docs/MVP_IMPLEMENTATION_FREEZE.md
Math:
docs/MVP_MATH_SPEC.md
Website:
docs/WEBSITE_IMPLEMENTATION_PLAN.md
Team:
docs/TEAM_CHARTER.md
Freeze:
docs/FINAL_FREEZE.md
---
## Local Development
Frontend:
```bash
cd frontend
npm install
npm run dev
```
Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
---
## License
MIT
---
## Status
Hackathon MVP
Architecture Frozen
Implementation In Progress