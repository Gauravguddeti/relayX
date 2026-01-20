---
name: frontend-visual-clarity-check
description: Checks frontend UI for font readability issues, color contrast failures, and inconsistent visual flow. Use when validating UI accessibility, design consistency, or pre-release frontend quality.
---

# Frontend Visual Clarity Check Skill

This skill evaluates whether text elements are readable against their background colors and whether the layout maintains a clear, linear visual structure across the frontend.

## When to use this skill

- When reviewing a new UI design, component, or page layout
- When validating accessibility and readability compliance
- When checking if fonts blend into background colors or reduce legibility
- When ensuring consistent visual hierarchy and linear content flow
- Before shipping frontend changes to production

## What this skill checks

### 1. Font & Background Contrast
- Detects low contrast between text color and background color
- Flags cases where text visually merges into the background
- Evaluates contrast ratios using WCAG 2.1 guidelines:
  - Normal text: minimum 4.5:1
  - Large text (≥18px or bold ≥14px): minimum 3:1

### 2. Font Consistency
- Ensures consistent font families across similar components
- Flags excessive font size variance within the same hierarchy level
- Detects inconsistent font weights used for identical semantic roles

### 3. Linear Visual Flow
- Verifies that content follows a top-to-bottom, left-to-right reading order
- Flags broken hierarchy where headings, subheadings, and body text are visually ambiguous
- Detects layout jumps caused by misaligned margins, padding, or spacing

### 4. Background Interference
- Flags text placed over:
  - Gradients
  - Images
  - Patterns
  without sufficient overlays or contrast safeguards
- Recommends solid overlays or contrast-enhancing techniques when needed

## How to use this skill

1. Identify the frontend surface:
   - Page, component, modal, or full application

2. Inspect computed styles:
   - Text color
   - Background color or layer stack
   - Font size, weight, and family

3. Calculate contrast ratios:
   - Compare text color vs final rendered background
   - Include overlays, opacity, and gradients in calculation

4. Evaluate hierarchy:
   - Headings should be visually dominant
   - Body text should not compete with headers
   - Call-to-action text should be distinct but readable

5. Report issues in this format:
   - **Issue type** (Contrast / Hierarchy / Flow / Consistency)
   - **Element selector or location**
   - **Why it fails**
   - **Recommended fix**

## Output conventions

- Be specific, not philosophical
- Prefer actionable fixes over generic advice
- Reference exact CSS properties when possible
- Prioritize readability over aesthetic intent

## Example Fix Recommendations

- Increase contrast by adjusting text color or background shade
- Add semi-transparent overlays behind text on images
- Normalize font sizes using a defined scale (e.g., 12 / 14 / 16 / 20 / 24)
- Enforce a single primary font family per surface
- Use consistent spacing tokens to maintain linear flow

---

This skill exists to prevent “it looked fine on my screen” from becoming a production incident.
