# MVP_MATH_SPEC.md
Version: 1.0
Status: FROZEN
---
# Purpose
Define the mathematical behavior of the Mantle Sentinel MVP.
The MVP intentionally uses simple, explainable algorithms.
Complex research systems are explicitly excluded.
---
# Goals
Provide:
- Alert scoring
- Agent confidence
- Consensus calculation
- Memory relevance ranking
using deterministic formulas.
---
# Severity Encoding
String severities are converted to numeric values.
| Severity | Score |
| -------- | ----- |
| low      | 1     |
| medium   | 2     |
| high     | 3     |
| critical | 4     |
---
# Agent Output Model
Each agent produces:
```json
{
  "agent_id": "security",
  "severity": 3,
  "confidence": 0.82,
  "reasoning": "Suspicious authentication activity detected."
}
```
---
# Confidence Range
Allowed:
0.0 ≤ confidence ≤ 1.0
Validation:
confidence must be clamped.
---
# Consensus Engine
Weighted average.
Formula:
consensus_score =
Σ(severity × confidence)
/
Σ(confidence)
Example:
Security:
severity=4
confidence=0.9
Infrastructure:
severity=2
confidence=0.5
Operations:
severity=3
confidence=0.7
Result:
(4×0.9 + 2×0.5 + 3×0.7)
/
(0.9+0.5+0.7)
= 3.19
Rounded:
3
Final Severity:
high
---
# Severity Mapping
| Range | Final Severity |
| ----- | -------------- |
| <1.5  | low            |
| <2.5  | medium         |
| <3.5  | high           |
| >=3.5 | critical       |
---
# Consensus Confidence
Average confidence.
Formula:
Σ(confidence)
/ n
Example:
(0.9+0.5+0.7)
/3
=0.7
---
# Disagreement Score
Purpose:
Measure agent disagreement.
Formula:
max(severity)
-
min(severity)
Example:
4-2
=2
---
# Disagreement Levels
| Score | Meaning   |
| ----- | --------- |
| 0     | Agreement |
| 1     | Minor     |
| 2     | Moderate  |
| 3     | Severe    |
---
# Memory Relevance
Simple scoring.
Formula:
relevance =
0.7 * similarity
+
0.3 * recency
---
# Similarity
Returned by vector search.
Range:
0.0–1.0
---
# Recency
Formula:
1/(1+days_old)
Examples:
0 days → 1.0
1 day → 0.5
7 days → 0.125
30 days → 0.032
---
# Ranking
Sort descending by relevance.
Top N returned.
Default:
N=5
---
# Alert Priority Score
Formula:
priority =
severity_score
×
confidence
Examples:
critical + 0.9
4 × 0.9 = 3.6
medium + 0.6
2 × 0.6 = 1.2
---
# Dashboard Ordering
Alerts sorted by:
1 Priority Score
then
2 Timestamp
---
# Out Of Scope
BOCPD
Bayesian Change Detection
Forecasting
Dream Mode
Simulation
Autonomous Planning
Reinforcement Learning
Agent Evolution
Probabilistic Graphs
---
# Success Criteria
All calculations deterministic.
All calculations explainable.
Results reproducible.
No external ML dependency required.
