---
name: frontend_design
description: Design distinctive, production-grade interfaces for Viktor Spaces and frontend codebases. Use when building or polishing dashboards, app surfaces, UI components, settings pages, or HTML/CSS/React/Tailwind frontends. Do NOT use for backend-only work or conversion-focused marketing pages where landing_page_design is a better fit.
---

Use this skill when the work is primarily about the interface itself: visual direction, layout, typography, spacing, interaction polish, or turning a rough UI into something intentional and memorable.

If you are working inside a Viktor Space, read the project README first and stay within the existing app stack. Reuse the app's components and tokens when they exist; extend them deliberately instead of fighting them.

If the task is really a marketing page, hero section, signup funnel, launch page, or splash page, read `skills/landing_page_design/SKILL.md` as well.

## Instructions

### Step 1: Understand the product surface

Before writing code, identify:

- what the interface is for
- who uses it
- what actions matter most
- whether the page is a product UI, internal tool, dashboard, or settings surface

If the request is underspecified, ask a small batch of questions about audience, tone, constraints, and must-have content.

### Step 2: Commit to an aesthetic direction

Do not drift into generic "AI app" styling. Pick a clear point of view and execute it consistently.

Good directions include:

- refined and editorial
- technical and industrial
- soft and calm
- dense and information-rich
- playful and tactile
- brutalist and raw
- premium and minimal

The key is intentionality, not loudness.

### Step 3: Design the system before the screens

Establish the foundation first:

- typography pairings
- color palette and contrast rules
- spacing scale
- border radius and shadow language
- interaction states
- reusable layout patterns

Prefer CSS variables or project tokens over scattered hardcoded values.

### Step 4: Build for the actual stack

For Viktor Spaces:

- prefer the existing Tailwind and shadcn patterns already in the project
- keep component boundaries clean
- use responsive layouts from the start
- make sure the page still feels coherent with the rest of the app

For other frontend codebases:

- match the local framework and styling approach
- reuse existing primitives before creating new abstractions
- keep the implementation production-grade, not demo-grade

### Step 5: Make the interface feel designed

Focus on:

- typography with personality and hierarchy
- strong spacing and alignment
- meaningful contrast and visual rhythm
- backgrounds, texture, or depth that support the concept
- polished hover, focus, loading, and empty states

Avoid:

- default-looking Inter-on-white layouts unless the project already uses that system intentionally
- purple-gradient-on-white SaaS cliches
- cookie-cutter card grids with no visual hierarchy
- decorative effects that fight readability or performance

### Step 6: Verify usability

Before finishing, check:

- mobile and desktop layouts both work
- primary actions are obvious
- text remains readable at realistic content lengths
- focus states and contrast are acceptable
- the interface still works without animation

### Step 7: Finish with polish

Do a final pass specifically for polish:

- tighten copy and labels
- remove awkward spacing
- balance alignment and density
- improve empty states and section transitions
- make one or two memorable choices instead of ten random ones

## Practical Heuristics

- A small number of strong visual decisions beats many weak ones.
- Distinctive typography is often the fastest way to improve a UI.
- The layout should communicate importance before the user reads the text.
- If every section uses the same card, padding, and heading pattern, the page will feel flat.
- Motion should clarify and delight, not create noise.

## Examples

### Example: Viktor Space dashboard

User says: "Build a cleaner dashboard for this Space."

Actions:

1. Read the Space README and inspect the existing component stack.
2. Choose an intentional direction that fits the product.
3. Define clearer hierarchy for the hero area, metrics, filters, and tables.
4. Improve typography, spacing, states, and responsiveness.

Result:
A dashboard that feels product-quality, not template-generated.

### Example: Settings or admin screen

User says: "This settings page works but looks bad."

Actions:

1. Keep the existing logic.
2. Improve grouping, hierarchy, labels, and interaction states.
3. Use section structure, consistent controls, and better spacing.

Result:
A settings page that is easier to scan and feels coherent with the rest of the app.

## Edge Cases

- If the project already has a strong design system, follow it instead of imposing a new aesthetic.
- If the user wants something deliberately simple, keep it restrained but still intentional.
- If the page is half product UI and half marketing, use this skill for the product sections and `landing_page_design` for the conversion-oriented sections.
<!-- ══════════════════════════════════════════════════════════════════════════
     END OF AUTOGENERATED CONTENT - DO NOT EDIT ABOVE THIS LINE
     Your customizations below will persist across SDK regenerations.
     ══════════════════════════════════════════════════════════════════════════ -->
