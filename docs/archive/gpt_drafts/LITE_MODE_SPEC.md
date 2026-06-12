# LITE_MODE_SPEC.md
Version: 1.0
Status: OPTIONAL POST-MVP
---
# Purpose
Lite Mode provides a low-resource monitoring interface.
Target devices:
- Older laptops
- Low-memory systems
- Mobile browsers
- Accessibility-first users
---
# Philosophy
Same data.
Different renderer.
Lite Mode is NOT a separate product.
Lite Mode is a separate frontend.
---
# Goals
Fast loading.
Minimal JavaScript.
Server-rendered pages.
Accessible by default.
---
# Technology
Framework:
Astro 4
UI:
React Islands
Styling:
CSS
Hosting:
Vercel
---
# Routes
/lite
/lite/alerts
/lite/agents
/lite/evolution
/lite/compare
/lite/admin
---
# Data Source
Uses same API.
https://api.mantlesentinel.ai
No duplicate backend.
---
# Functional Scope
View alerts.
View agents.
View consensus.
View evolution history.
View system health.
---
# Excluded
Editing
Administration
Training
Agent configuration
Dream Mode
BOCPD
---
# Performance Targets
First Load:
<100KB
LCP:
<1.5s
TTI:
<2s
---
# Accessibility
Keyboard navigation.
WCAG AA.
Screen readers.
Reduced motion.
---
# Deployment
Optional.
Post-MVP.
Not required for hackathon submission.