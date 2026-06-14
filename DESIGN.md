# Mantle Sentinel — DESIGN.md
# Behavioral threat monitor. Dark, technical, alive.

## Overview

Mantle Sentinel is a real-time AI security agent for DeFi smart contracts. The visual language is
borrowed from professional security monitoring dashboards (Grafana, Datadog, Wireshark) — not from
generic SaaS. The page must feel like live software, not a brochure.

**Brand personality:** Silent watcher. Decisive striker. Not a startup, a sentinel.
**Audience:** DeFi protocol teams, security engineers, hackathon judges (AI/security track).
**Anti-pattern to avoid:** Generic AI-startup glow cards, purple-pink gradients, emoji bullets,
testimonial carousels, inter-only typography, stats bars with no context, hero with big rounded number.

---

## Color System

```
canvas:        #090909    /* near-void black — base surface */
surface-1:     #111111    /* card background */
surface-2:     #161616    /* elevated panel */
surface-3:     #1e1e1e    /* hover state */
hairline:      #2a2a2a    /* border default */
hairline-soft: #1f1f1f    /* subtle border */

ink:           #f0f0ef    /* primary text */
ink-muted:     #8a8a8a    /* secondary text */
ink-subtle:    #555555    /* tertiary / metadata */

accent:        #f97316    /* amber-500 — SINGLE brand color for alerts, CTAs, key numbers */
accent-hover:  #fb923c    /* amber-400 */
accent-dim:    rgba(249,115,22,0.12) /* accent tint for bg glow */

ok:            #22c55e    /* green-500 — healthy state */
ok-dim:        rgba(34,197,94,0.10)
alert:         #ef4444    /* red-500 — anomaly state */
alert-dim:     rgba(239,68,68,0.10)
cyan:          #06b6d4    /* mascot glow only — not for UI accent */
```

**Rule:** `accent` (amber) appears on CTAs, alert numbers, key data points. Never as decoration.
`ok` appears only on status indicators. `alert` appears only on anomaly states. `cyan` is reserved
for the mascot glow exclusively.

---

## Typography

```
display:   "Space Grotesk", sans-serif   — weights 500 700, tracking -0.03em to -0.05em
           (Google Fonts, load 500+700)
mono:      "JetBrains Mono", monospace  — weight 400 500
           (Google Fonts, used for ALL data: hashes, numbers, scores, block IDs, code)
body:      "Inter", sans-serif           — weight 400 only
           (Google Fonts, used for prose descriptions only)
```

**Scale:**
```
hero-headline:  clamp(40px, 6vw, 72px), Space Grotesk 700, tracking -0.04em, line-height 1.05
section-title:  clamp(28px, 4vw, 44px), Space Grotesk 700, tracking -0.03em
card-title:     20px, Space Grotesk 500, tracking -0.02em
body:           16px, Inter 400, line-height 1.6
mono-data:      13–15px, JetBrains Mono 400, line-height 1.4
mono-label:     11px, JetBrains Mono 500, tracking 0.08em, UPPERCASE
```

**Rule:** Prose descriptions → Inter. Everything that looks like data (numbers, scores, addresses,
block IDs, function names) → JetBrains Mono. Section headings → Space Grotesk.
Never use Plus Jakarta Sans or Inter for headlines — it reads as generic SaaS.

---

## Spacing

Base unit: 4px. Scale: 4 8 12 16 24 32 48 64 96 128px.
Section vertical rhythm: 96px padding-top/bottom minimum.
Container max-width: 1200px. Content max-width: 760px for text-heavy sections.

---

## Border Radius

```
sharp:   0px   (terminal blocks, data tables, timeline rail)
small:   4px   (tags, badges, inline code)
medium:  6px   (cards, panels)
pill:    999px (status dots, toggle buttons only)
```
**Rule:** No rounded-2xl or rounded-xl on content cards. Max 6px. Sharp edges signal precision.

---

## Shadows & Depth

```
card-idle:   0 1px 0 #2a2a2a  (just a hairline bottom — flat, purposeful)
card-hover:  0 0 0 1px #f97316, 0 4px 24px rgba(249,115,22,0.08)
             (amber border traces on hover — no floating box shadows)
glow-ok:     0 0 16px rgba(34,197,94,0.20)
glow-alert:  0 0 16px rgba(239,68,68,0.30)
glow-mascot: drop-shadow(0 0 12px #06b6d4)  (CSS filter on PNG)
```

**Rule:** No diffuse box-shadows lifting cards. Depth via border-color changes only.

---

## Motion

```
reveal:        opacity 0→1 + translateY 20px→0, 0.55s cubic-bezier(0.22,1,0.36,1)
               triggered by IntersectionObserver, threshold 0.15
data-update:   color flash to accent then fade, 0.3s ease — for live feed numbers
counter:       requestAnimationFrame linear from 0 to target, 1.2s
mascot-float:  translateY -6px → 6px, 5s ease-in-out infinite
mascot-glow:   drop-shadow 4px → 16px → 4px, 3s ease-in-out infinite
mascot-alert:  filter brightness(2) hue-rotate(160deg) → normal, 0.25s, once on ALERT
pipeline-fill: stroke-dashoffset 100%→0%, 0.8s ease — for SVG connector lines
```

**Rule:** `prefers-reduced-motion` guard on all animations. No auto-playing video. No parallax.

---

## Component Patterns

### Terminal Block (used in Hero and Pipeline sections)
```css
background: #111111;
border: 1px solid #2a2a2a;
border-radius: 4px;
font-family: "JetBrains Mono";
font-size: 13px;
color: #f0f0ef;
padding: 16px 20px;
```
Green "cursor" blinks at end of last line (`::after`, opacity 0/1, 1s step-end infinite).
Top-left: three dots (red #ef4444, yellow #f97316, green #22c55e), 8px circles, gap 6px.

### Status Badge
```
● LIVE     — dot #22c55e, text ink-muted, JetBrains Mono 11px uppercase
● ANOMALY  — dot #ef4444 with glow-alert, text accent, animated pulse
● MONITOR  — dot #f97316, text ink-muted
```

### Data Card
```
surface-1 bg, 1px hairline border, border-radius 6px,
padding 24px, hover: border-color accent + box-shadow card-hover
```
Header: mono-label (uppercase, ink-subtle). Value: mono-data (ink or accent). 
No icons unless SVG (no emoji, no icon fonts).

### Primary CTA Button
```
background: #f97316, color: #090909, font: Space Grotesk 600 15px,
padding: 12px 24px, border-radius: 4px, letter-spacing: -0.01em
hover: background #fb923c, transition 0.15s
```

### Ghost Button
```
background: transparent, border: 1px solid #2a2a2a, color: #f0f0ef,
same font/padding/radius. hover: border-color #555555
```

---

## Page Structure (order matters for conversion)

```
1. NAV          — logo + links + "View on GitHub" ghost
2. HERO         — hook statement + terminal live log + mascot + proof strip
3. PROBLEM      — 2-column: "what happened" vs "what Sentinel saw" (Euler case study)
4. WHY US       — 3-point differentiation vs rule-based / LSTM (no icon cards)
5. PIPELINE     — vertical scroll-journey T0→T5 with sticky rail
6. LIVE DEMO    — canvas chart + tx stream feed
7. PROOF        — benchmark numbers with context + on-chain anchor
8. CTA          — single focused action (DoraHacks + GitHub)
9. FOOTER
```

**Removed vs v3:** stats-bar (numbers without context), 6 benefit-cards (generic), Formspree email
capture (no backend = abandoned SaaS signal), Eye View toggle (complexity without clarity).

---

## Voice & Copy Rules

- Short declarative sentences. Active verbs. Present tense.
- No "revolutionary", "cutting-edge", "leverage", "harness", "unlock potential".
- Numbers always appear in JetBrains Mono, even inline in prose.
- Every metric has a context annotation: "4.3× — vs FreqBase rule-based baseline".
- Euler $197M is the proof-of-concept kicker, not a statistic.

---

## Do / Don't

| ✅ DO | ❌ DON'T |
|-------|---------|
| Near-void black (#090909) base | Dark gradients (purple→black, etc.) |
| Single amber accent | Three+ brand colors simultaneously |
| JetBrains Mono for all data | Display font for numbers/hashes |
| Sharp 4–6px corners on cards | rounded-2xl / rounded-xl cards |
| Border-color hover on cards | Box-shadow lift on hover |
| Terminal block for hero content | Hero text on gradient background |
| Context annotation per metric | Bare stats-bar with 4 numbers |
| Inline SVG or PNG (no icon fonts) | Emoji as UI icons |
| Proof before explanation (demo early) | Pipeline before demo |
| Space Grotesk for headings | Inter or Plus Jakarta Sans for headings |
