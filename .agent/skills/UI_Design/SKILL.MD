---
name: formal-minimalist-design
description: >
  A strict formal minimalist design system for building document-centric, high-contrast frontend UIs.
  Use this skill whenever the user asks to build or style a UI with a "formal", "document-like",
  "minimal", "professional", "no-frills", or "report-style" aesthetic. Also triggers for CV/resume
  tools, data analysis dashboards, internal tools, scoring apps, or any interface where clarity and
  information hierarchy matter more than visual flair. Apply this skill before writing any CSS,
  HTML component, Streamlit layout, or React component in these contexts — even if the user just says
  "make it look clean and professional."
---

# Formal Minimalist Design Skill

A rigorous visual system for building **document-centric**, **high-contrast**, **flat** frontends.
The core premise: the UI should feel like a well-typeset physical report — not a consumer web app.

---

## 1. Core Principles (Read First)

| Principle | Rule |
|---|---|
| Utility over Decoration | Every visual element must serve hierarchy or information. Remove anything else. |
| Document-Centricity | Interface should feel like reading a formal report or terminal output. |
| Maximum Contrast | Rely on black/white contrast, not color, to guide the eye. |
| Typography as Primary UI | Font size, weight, and casing establish all visual hierarchy. |
| No Depth | Flat design only. No shadows, no gradients, no perceived depth. |

---

## 2. Design Tokens

### 2.1 Color Variables

```css
:root {
  /* Backgrounds */
  --color-bg-primary:    #FFFFFF;   /* Main content area */
  --color-bg-secondary:  #F9FAFB;   /* Sidebars, secondary sections */

  /* Text */
  --color-text-primary:  #000000;   /* Headings, key data */
  --color-text-secondary:#4B5563;   /* Body, descriptions, metadata */

  /* Borders */
  --color-border-default:#D1D5DB;   /* Standard panel/input borders */
  --color-border-strong: #000000;   /* Focus states, critical dividers */

  /* Actions */
  --color-action-primary:#000000;   /* Button background */
  --color-action-hover:  #374151;   /* Button hover */

  /* Spacing */
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
}
```

### 2.2 Status Colors (Minimal Use — Text Only)

```css
:root {
  --status-pass-text: #065f46;  /* Use with label: [PASS] or [STRONG] */
  --status-warn-text: #92400e;  /* Use with label: [REVIEW] */
  --status-fail-text: #991b1b;  /* Use with label: [ISSUE] or [WEAK] */
}
```

> **Rule:** Never use status colors as backgrounds. Text labels only.
> Prefer conveying status via text: `Status: Rejected` rather than colored indicators.

### 2.3 Typography Scale

```css
/* Display Title — Page-level heading */
.display-title {
  font-size: 28px;
  font-weight: 700;
  color: #000000;
  letter-spacing: -0.02em;
}

/* H1 — Section header with top border */
h1 {
  font-size: 20px;
  font-weight: 700;
  color: #000000;
  border-top: 2px solid #000000;
  padding-top: 16px;
}

/* H2 — Panel header, uppercase */
h2 {
  font-size: 16px;
  font-weight: 600;
  color: #000000;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Body */
p, li, td {
  font-size: 14px;
  font-weight: 400;
  color: #4B5563;
  line-height: 1.6;
}

/* Data Label */
.data-label {
  font-size: 12px;
  font-weight: 600;
  color: #4B5563;
  text-transform: uppercase;
}

/* Data Value */
.data-value {
  font-size: 18px;
  font-weight: 700;
  color: #000000;
}
```

Font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`

---

## 3. Component Patterns

### 3.1 Buttons

```css
button, .btn {
  background: #000000;
  color: #FFFFFF;
  border: 1px solid #000000;
  border-radius: 0px;
  font-weight: 600;
  font-size: 14px;
  padding: 8px 16px;
  box-shadow: none;
  transition: background 0.1s ease;
  cursor: pointer;
}

button:hover {
  background: #374151;
}
```

> No transform, no lift, no glow on hover.

### 3.2 Inputs & Textareas

```css
input, textarea, select {
  border: 1px solid #D1D5DB;
  border-radius: 0px;
  background: #FFFFFF;
  font-size: 14px;
  padding: 8px 12px;
  outline: none;
  box-shadow: none;
  font-family: inherit;
}

input:focus, textarea:focus {
  border-color: #000000;
}
```

### 3.3 Panels / Cards

```css
.panel, .card {
  border: 1px solid #D1D5DB;
  border-radius: 0px;
  background: #FFFFFF;
  padding: 16px;
  box-shadow: none;
}
```

Use borders for separation — never shadows.

### 3.4 Progress Bars

```css
/* Track */
.progress-track {
  background: #E5E7EB;
  border-radius: 0px;
  height: 8px;
}

/* Fill */
.progress-fill {
  background: #000000;
  border-radius: 0px;
  height: 8px;
}
```

### 3.5 Tables

```css
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 14px;
}

th {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: #4B5563;
  border-bottom: 2px solid #000000;
  padding: 8px 12px;
  text-align: left;
}

td {
  border-bottom: 1px solid #D1D5DB;
  padding: 8px 12px;
  color: #4B5563;
}
```

### 3.6 Badges / Status Tags

```css
/* Render as inline text labels only */
.badge {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  padding: 2px 6px;
  border: 1px solid currentColor;
  border-radius: 0px;
  background: transparent;
}

.badge-pass  { color: #065f46; }
.badge-warn  { color: #92400e; }
.badge-fail  { color: #991b1b; }
```

---

## 4. Layout Patterns

### 4.1 Two-Column (Input + Results)

```
┌─────────────────────┬──────────────────────────────┐
│   INPUT AREA        │   RESULTS PANEL              │
│   (JD / CV text)    │   Score, Breakdown, Flags    │
│                     │                              │
│   [ANALYSE]         │   [PASS] / [FAIL] labels     │
└─────────────────────┴──────────────────────────────┘
```

- Left column: input fields, action button
- Right column: structured score output with Data Labels + Data Values
- Divider: `1px solid #D1D5DB` vertical line or simple padding gap

### 4.2 Stacked Report View

For single-column results (score report, CV breakdown):

```
────────────────────────────────────
SECTION TITLE                     (H1 with top border)

  Label              Value
  Label              Value

────────────────────────────────────
NEXT SECTION
  ...
```

---

## 5. Streamlit-Specific Overrides

When implementing in Streamlit via `st.markdown('<style>...</style>')`, apply this reset first:

```css
/* Reset Streamlit defaults */
.stButton > button {
  background: #000000 !important;
  color: #FFFFFF !important;
  border-radius: 0px !important;
  border: 1px solid #000000 !important;
  box-shadow: none !important;
  font-weight: 600 !important;
}

.stButton > button:hover {
  background: #374151 !important;
  border-color: #374151 !important;
}

.stTextArea textarea,
.stTextInput input {
  border-radius: 0px !important;
  border: 1px solid #D1D5DB !important;
  box-shadow: none !important;
}

.stTextArea textarea:focus,
.stTextInput input:focus {
  border-color: #000000 !important;
  box-shadow: none !important;
}

.stProgress > div > div {
  border-radius: 0px !important;
  background: #000000 !important;
}

.stProgress > div {
  border-radius: 0px !important;
}

[data-testid="stExpander"] {
  border-radius: 0px !important;
  border: 1px solid #D1D5DB !important;
}
```

---

## 6. Anti-Pattern Checklist

Before finalizing any UI, verify:

- [ ] **No emojis** — Replace `🚀 Start` with `START ANALYSIS`
- [ ] **No gradients** — `linear-gradient` and `radial-gradient` are banned
- [ ] **No shadows** — `box-shadow: none` everywhere
- [ ] **No rounded corners** — `border-radius: 0px` on all elements
- [ ] **No pastel/vibrant colors** — Only grayscale + the 3 status text colors
- [ ] **No micro-animations** — No hover lifts, floats, or transitions > 0.15s
- [ ] **No decorative icons** — Text labels only; no emoji stand-ins

---

## 7. Implementation Workflow

Follow these steps in order for any new UI build:

1. **Define information hierarchy** — List all data points and rank by importance
2. **Set up CSS variables** — Paste the token block from Section 2 at the top of your stylesheet
3. **Apply typography** — Assign heading levels before touching layout
4. **Build structure** — Grid or flex layout using the patterns in Section 4
5. **Add components** — Buttons, inputs, panels using Section 3
6. **Strip decoration** — Run the anti-pattern checklist from Section 6
7. **Verify contrast** — All text must be legible on white background without color crutches

---

## 8. Quick Reference Card

| Element | Value |
|---|---|
| Background | `#FFFFFF` |
| Secondary BG | `#F9FAFB` |
| Primary text | `#000000` |
| Body text | `#4B5563` |
| Border | `1px solid #D1D5DB` |
| Strong border | `1px solid #000000` |
| Button bg | `#000000` |
| Button hover | `#374151` |
| Border radius | `0px` |
| Shadow | `none` |
| Pass color | `#065f46` (text only) |
| Warn color | `#92400e` (text only) |
| Fail color | `#991b1b` (text only) |