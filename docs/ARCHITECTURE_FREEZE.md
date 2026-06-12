# Mantle Sentinel
# Architecture Freeze v1.0
Status: FROZEN
Date: Hackathon Build Freeze
---
## Purpose
This document defines the frozen MVP architecture.
Anything not listed here is outside MVP scope.
---
# System Overview
Mantle Sentinel consists of six layers:
```text
Observation Layer
        ↓
Prediction Layer
        ↓
Debate Layer
        ↓
Memory Layer
        ↓
Evolution Layer
        ↓
Alert Layer
        ↓
Dashboard
```
Each layer produces visible artifacts.
---
# Layer 1 — Observation Layer
Purpose:
Generate structured observations.
Input:
- external events
- simulated events
- scheduled events
Output:
```json
{
  "event_id":"evt_001",
  "type":"game",
  "subject":"LAL vs DEN",
  "timestamp":"2026-06-01T12:00:00Z"
}
```
MVP Source:
Mock Generator
No external integrations required.
---
# Layer 2 — Prediction Layer
Purpose:
Generate agent predictions.
Input:
Observation
Output:
```json
{
  "agent_id":"bolt",
  "prediction":"LAL -3.5",
  "confidence":82,
  "reasoning":"pace mismatch"
}
```
Rules:
- deterministic
- explainable
- reproducible
No LLM required.
Prediction templates are sufficient.
---
# Layer 3 — Debate Layer
Purpose:
Compare predictions.
Detect:
- agreement
- disagreement
- conflict
Example:
Agent A
LAL -3.5
Agent B
LAL +1.0
Result:
```json
{
  "type":"disagreement",
  "severity":"high"
}
```
Visible in dashboard.
---
# Layer 4 — Memory Layer
Purpose:
Store history.
Memory Unit:
```json
{
  "memory_id":"mem_001",
  "agent_id":"bolt",
  "event_type":"prediction",
  "timestamp":"..."
}
```
Storage:
PostgreSQL
Optional:
NetworkX graph representation.
Required MVP Features:
- insert memory
- retrieve memory
- count memories
No semantic retrieval.
No vector database.
---
# Layer 5 — Evolution Layer
Purpose:
Track agent progression.
Triggers:
- prediction count
- accuracy threshold
- memory count
Example:
```json
{
  "agent_id":"bolt",
  "old_level":2,
  "new_level":3
}
```
Evolution must be visible.
No autonomous self-modification.
---
# Layer 6 — Alert Layer
Purpose:
Generate notable events.
Alert Types:
1. Confidence Spike
2. Strong Disagreement
3. Evolution Event
4. Activity Surge
Output:
```json
{
  "alert_type":"evolution",
  "severity":"medium"
}
```
All alerts visible.
---
# Dashboard
Primary User Interface
Sections:
1. Agent Overview
2. Predictions Feed
3. Disagreement Feed
4. Evolution Feed
5. Alert Feed
---
# Agent Model
Required Fields
```json
{
  "id":"bolt",
  "name":"Bolt",
  "level":2,
  "confidence":82,
  "memory_count":123
}
```
Optional Fields
```json
{
  "style":"balanced",
  "risk":0.4
}
```
---
# Storage
PostgreSQL
Tables:
agents
predictions
memories
evolution_events
alerts
No vector DB.
No graph DB.
---
# Background Jobs
Worker Loop
Interval:
30 seconds
Responsibilities:
- create observations
- generate predictions
- run debates
- update memory
- emit alerts
Single worker process.
---
# API
Read APIs only.
GET /agents
GET /agents/:id
GET /predictions
GET /alerts
GET /evolution
GET /health
---
# Explicit Exclusions
Dream Mode
BOCPD
RL
Fine Tuning
Autonomous Planning
Multi Region Deployment
Microservices
Kubernetes
Vector Search
LLM Tool Use
Production Scaling
---
# Architecture Decision
Visible behavior > sophisticated implementation.
Everything must be observable.