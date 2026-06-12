# WEBSITE_IMPLEMENTATION_PLAN.md
Version: 1.0
Status: FROZEN
---
# Purpose
The website serves as the public-facing presentation layer for Mantle Sentinel.
Its purpose is to:
1. Explain the project.
2. Demonstrate live system behavior.
3. Showcase architecture.
4. Support hackathon judging.
5. Direct users to documentation and source code.
The website is not the monitoring application.
The website is a communication and demonstration layer.
---
# Primary Audience
## Hackathon Judges
Need:
* Quick understanding
* Architecture visibility
* Technical credibility
---
## Developers
Need:
* Documentation
* Repository access
* System understanding
---
## Future Contributors
Need:
* Project context
* Technical roadmap
* Clear onboarding
---
# Website Goals
Visitors should understand:
* What Mantle Sentinel does
* Why it matters
* How it works
* Why multi-agent consensus is useful
within 60 seconds.
---
# Domains
Production:
https://mantlesentinel.ai
Application:
https://app.mantlesentinel.ai
API:
https://api.mantlesentinel.ai
Documentation:
https://docs.mantlesentinel.ai
Repository:
https://github.com/alexbelij/mantle-sentinel
---
# Technology Stack
Frontend:
* Next.js 15
* TypeScript
* TailwindCSS
* shadcn/ui
Hosting:
* Vercel
Monitoring:
* Sentry
Analytics:
* Plausible
---
# Site Map
/
Landing Page
/about
Project Overview
/architecture
System Architecture
/live
Live Monitoring Demo
/agents
Agent Directory
/docs
Documentation Hub
/github
External Redirect
/status
System Status
---
# Landing Page
Purpose:
Explain Mantle Sentinel immediately.
---
## Section 1 — Hero
Headline:
Mantle Sentinel
Subheadline:
Multi-Agent Monitoring System for Intelligent Alert Analysis
Primary CTA:
View Live Demo
Secondary CTA:
View Architecture
---
## Section 2 — Problem
Organizations receive:
* Too many alerts
* Too much noise
* Too many false positives
Human operators become overloaded.
Important incidents can be missed.
---
## Section 3 — Solution
Mantle Sentinel introduces:
Specialized AI Agents
Each agent focuses on a domain:
* Security
* Infrastructure
* Operations
Agents analyze independently.
Consensus combines results.
---
## Section 4 — Architecture
Visual Flow:
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
---
## Section 5 — Live Monitoring Preview
Displays:
Recent Alerts
Agent Decisions
Consensus Outcomes
Current System Status
Data pulled from backend API.
---
## Section 6 — Multi-Agent System
Agent Cards:
Router Agent
Security Agent
Infrastructure Agent
Operations Agent
Consensus Agent
Each card contains:
Role
Description
Current Status
---
## Section 7 — Technical Stack
Frontend
Backend
Storage
Monitoring
Deployment
Displayed as architecture cards.
---
## Section 8 — Demo Video
Embedded video.
Length:
3–5 minutes.
Contents:
Problem
Architecture
Demo
Future Vision
---
## Section 9 — Documentation
Links:
Architecture Freeze
Implementation Freeze
Math Spec
Team Charter
Final Freeze
---
## Section 10 — GitHub
Repository Link
Latest Commit
License
Documentation Access
---
# About Page
Purpose:
Explain project motivation.
Sections:
Problem
Vision
Approach
Architecture
Future Roadmap
---
# Architecture Page
Purpose:
Explain internal design.
Contains:
System Diagram
Agent Diagram
Consensus Diagram
Memory Diagram
API Diagram
---
# Live Monitoring Page
Purpose:
Demonstrate system behavior.
Displays:
Recent Alerts
Agent Predictions
Consensus Results
Confidence
Severity
Timestamp
Refresh:
Every 5 seconds.
Stretch Goal:
SSE updates.
---
# Agent Directory
Displays:
Agent Name
Role
Status
Memory Size
Recent Activity
Agent Profile Pages Optional.
Not required for MVP.
---
# Documentation Hub
Links to:
ARCHITECTURE_FREEZE.md
MVP_IMPLEMENTATION_FREEZE.md
MVP_MATH_SPEC.md
TEAM_CHARTER.md
FINAL_FREEZE.md
README.md
---
# GitHub Redirect
Simple redirect.
Target:
https://github.com/alexbelij/mantle-sentinel
---
# Status Page
Purpose:
Display operational status.
Metrics:
Backend Status
Database Status
API Status
Last Update Timestamp
---
# Design System
Colors:
Primary:
Slate
Secondary:
Blue
Accent:
Emerald
Danger:
Red
---
Typography:
Inter
Fallback:
System Sans
---
# Responsive Support
Required:
Mobile
Tablet
Desktop
Breakpoints:
320
640
768
1024
1440
---
# Accessibility
Requirements:
Keyboard Navigation
Screen Reader Support
ARIA Labels
Focus States
WCAG AA Compliance
---
# Performance Targets
Lighthouse:
> =90
LCP:
<2.5s
CLS:
<0.1
TTI:
<3s
---
# SEO
Required Pages:
Landing
About
Architecture
Documentation
Metadata:
Title
Description
OpenGraph
Twitter Cards
Sitemap
Robots.txt
---
# MVP Scope
Included:
Landing
Architecture
Live Monitoring
Documentation Hub
GitHub Link
Status Page
---
# Stretch Goals
Agent Profiles
Historical Charts
Interactive Architecture
SSE Live Feed
---
# Explicitly Excluded
Dream Mode
BOCPD
Research Features
Agent Evolution UI
Production Administration
Enterprise Features
---
# Deployment Plan
Frontend:
Vercel
Backend:
Railway
Database:
SQLite
Domain:
mantlesentinel.ai
---
# Success Criteria
A judge can:
Understand the project.
See architecture.
Observe live behavior.
Access source code.
Access documentation.
within five minutes.
Website deploys successfully.
Website supports the MVP demonstration.
No critical failures during judging.
