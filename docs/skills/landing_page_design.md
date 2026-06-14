---
name: landing_page_design
description: Design high-converting landing pages and marketing sections for HTML and Viktor Spaces projects. Use when writing or revising hero sections, splash pages, launch pages, waitlists, pricing pages, CTA flows, or full landing pages. Do NOT use for general product UI or dashboard work where frontend_design is a better fit.
---

Use this skill when the page's job is persuasion: explain value quickly, create trust, and move the visitor toward a single primary action.

If you are working inside a Viktor Space, this skill applies to marketing-style surfaces in that app. If you are building general app UI, dashboards, or settings screens, read `skills/frontend_design/SKILL.md` instead.

## Instructions

### Step 1: Clarify the conversion goal

Before designing the page, identify:

- who the visitor is
- what they want
- what pain they are trying to avoid
- the single primary CTA
- the proof points available

If these are missing, ask for them. Landing pages fail when the conversion goal is fuzzy.

### Step 2: Nail the above-the-fold section

Everything visible before scrolling should communicate value in a few seconds.

The hero should usually contain:

- a clear headline focused on the outcome
- a concise subheadline explaining how it works
- one primary CTA
- supporting trust or social proof
- a visual that reinforces the outcome

Avoid leading with a vague product screenshot or abstract filler artwork unless it directly supports the message.

### Step 3: Write conversion-oriented copy

Prefer copy that is specific and outcome-driven.

Good headline patterns:

- outcome without pain
- outcome in timeframe
- the better way to do a common task
- stop pain, start outcome

Avoid:

- empty buzzwords
- generic platform language
- headlines that describe the company instead of the benefit

CTA copy should use an action plus value:

- Start free
- Book a demo
- Create your first report
- Join the waitlist

### Step 4: Use a proven section flow

Default section order:

1. hero
2. trust or social proof
3. problem
4. solution or features
5. how it works
6. testimonials or proof
7. pricing or offer details
8. FAQ
9. final CTA

You can compress this for smaller pages, but do not scatter sections randomly.

### Step 5: Design for clarity first, aesthetics second

Landing pages should still look excellent, but the visuals must support conversion.

Focus on:

- a strong visual hierarchy
- one dominant CTA
- whitespace around the CTA and headline
- imagery or illustration that shows the outcome or desired state
- readable section transitions
- fast scanning on mobile

If a bold aesthetic choice hurts clarity, simplify it.

### Step 6: Build in a Viktor-friendly way

For raw HTML pages:

- use semantic HTML
- keep the structure easy to edit
- make responsive behavior obvious in the code

For Viktor Spaces:

- implement the marketing surface with the project's existing stack
- reuse tokens and components where possible
- keep the page lightweight and fast to load

Do not make the landing page feel like a dashboard with marketing copy pasted into it.

### Step 7: Add trust and reduce friction

Include trust signals where possible:

- customer logos
- user counts
- testimonials
- before/after outcomes
- compliance or reliability notes
- concise FAQ answers for common objections

Reduce friction by:

- minimizing form fields
- avoiding multiple competing CTAs
- repeating the primary CTA after major sections

### Step 8: Check mobile and performance

Before finishing, verify:

- headline and CTA remain clear on mobile
- tap targets are large enough
- hero content does not overflow
- page weight stays reasonable
- decorative assets do not block first paint

## Practical Heuristics

- One sharp promise converts better than five weak benefits.
- Visitors should know what the page is about before they hit the fold.
- Social proof belongs near decision points, not buried at the bottom.
- The best hero image usually shows the result or context, not just a UI screenshot.
- If you cannot support a claim with proof, soften the claim.

## Examples

### Example: Launch page for a new Viktor Space

User says: "Create a landing page for this Space before we share it."

Actions:

1. Identify the audience and the core workflow the Space unlocks.
2. Write an outcome-first headline and CTA.
3. Build a hero, feature blocks, proof section, and final CTA.
4. Make sure the page feels like a product launch page, not an internal tool screen.

Result:
A page that explains the value quickly and gives the user a clear next step.

### Example: Waitlist page in plain HTML

User says: "I need a simple waitlist page with good conversion."

Actions:

1. Keep the form minimal.
2. Emphasize the benefit and urgency.
3. Add concise trust signals and a clear CTA.
4. Optimize mobile spacing and hierarchy.

Result:
A lightweight page with one obvious action and minimal friction.

## Edge Cases

- If the user only wants a polished product UI, use `frontend_design` instead.
- If there is no real social proof yet, use precise product proof, concrete outcomes, or transparent positioning rather than inventing logos or numbers.
- If the page must be extremely minimal, keep the structure short but preserve headline, CTA, and trust.
<!-- ══════════════════════════════════════════════════════════════════════════
     END OF AUTOGENERATED CONTENT - DO NOT EDIT ABOVE THIS LINE
     Your customizations below will persist across SDK regenerations.
     ══════════════════════════════════════════════════════════════════════════ -->
