# Z.ai Prompt Template

Z.ai receives the **structured findings** produced by Sentinel's Tier-5
interpreter and returns a short, human-readable explanation of a confirmed
alert. The detection itself is purely algebraic — **no model is in the
detection loop**. Z.ai only *restates* the structured Tier-5 output in plain
English; it never decides whether an alert fires.

> Source of truth: [`sentinel/explain_zai.py`](../sentinel/explain_zai.py)
> (`explain_alert()`). This file is generated from that code — keep them in sync.

## Endpoint / model

| Setting        | Value (override via env)                       |
| -------------- | ---------------------------------------------- |
| `ZAI_BASE_URL` | `https://api.z.ai/api/paas/v4`                 |
| `ZAI_MODEL`    | `glm-4.5-flash` (free tier)                    |
| `max_tokens`   | `800` (GLM-4.5 reasoning models burn completion tokens on hidden thinking — a small cap can truncate the answer to empty) |
| `temperature`  | `0.3`                                           |
| timeout        | `10s`                                           |

If `ZAI_API_KEY` is unset (e.g. in CI) the explainer runs in **dry-run mode**
and returns a deterministic canned explanation — the live API is never touched.

## Input — Tier-5 `Alert` fields used

The prompt is built from a fully-populated `Alert` (see
[`sentinel/alert.py`](../sentinel/alert.py)):

```jsonc
{
  "contract":   "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9", // monitored address
  "alert_type": "spam_attack",        // spam_attack | entropy_anomaly | regime_shift
  "block":      96672007,             // window block number
  "drift":      0.871,                // drift score, float 0..1
  "branch":     "hamming",            // hamming | timing | entropy | spam
  "top_features": [                   // Tier-5 ablation attribution, highest first
    { "name": "selector_entropy", "contribution": 0.47 },
    { "name": "hamming_distance", "contribution": 0.31 }
  ]
}
```

## System prompt

```
You are a concise security explainer for blockchain monitoring alerts.
Report only what the data shows. Max 3 sentences.
```

## User prompt template

The user message is assembled with an f-string in `explain_alert()`
(`features_list` = the `name` of each entry in `top_features`):

```
Contract {alert.contract} triggered a {alert.alert_type} alert at block
{alert.block}. Drift score: {alert.drift:.3f} (branch: {alert.branch}).
Top contributing features: {features_list}. Explain in plain English for a
DeFi user.
```

### Rendered example

```
Contract 0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9 triggered a spam_attack
alert at block 96672007. Drift score: 0.871 (branch: hamming). Top
contributing features: ['selector_entropy', 'hamming_distance']. Explain in
plain English for a DeFi user.
```

## Request body (OpenAI-compatible `chat/completions`)

```json
{
  "model": "glm-4.5-flash",
  "messages": [
    { "role": "system", "content": "<system prompt above>" },
    { "role": "user",   "content": "<user prompt above>" }
  ],
  "max_tokens": 800,
  "temperature": 0.3
}
```

The response `choices[0].message.content` is trimmed and returned. On empty
content or any error the explainer falls back to the deterministic canned
explanation, so an alert always carries a human-readable message.
