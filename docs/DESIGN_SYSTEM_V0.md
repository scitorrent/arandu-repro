# Arandu Repro v0 – Design System

## 1. Brand & Mood

**Feeling:** When users visit Arandu Repro, they should feel they're using a tool that is trustworthy, calm, and purpose-built for serious scientific work. The interface should feel like a quiet laboratory—clean, organized, and focused on the task at hand.

**Tone adjectives:**
- **Calm** - No visual noise, generous whitespace, clear information hierarchy
- **Trustworthy** - Consistent, predictable interactions, clear feedback
- **Modern** - Contemporary design patterns, clean typography, subtle interactions
- **Purposeful** - Every element serves a clear function, no decoration for decoration's sake
- **Rooted** - Subtle connection to nature through color (moss green) without being literal

**Brand connection:**
The name "Arandu" (from Tupi-Guarani, meaning wisdom/deep knowledge) connects to themes of:
- **Forests and roots** - Deep, interconnected knowledge systems
- **Regeneration** - Science that builds on itself, reproducible and sustainable
- **Clarity** - Transparent processes, clear results, honest reporting

The UI should subtly evoke these themes through color choices (moss green) and organic, flowing layouts, while remaining professional and scientific.

---

## 2. Color System

### Core Palette

**Background & Surface:**
- `--color-bg-primary`: `#F9FAFB` - Main page background (very light gray)
- `--color-bg-secondary`: `#FFFFFF` - Cards, surfaces, elevated elements
- `--color-bg-tertiary`: `#F3F4F6` - Subtle backgrounds, hover states

**Text:**
- `--color-text-primary`: `#111827` - Main body text, headings
- `--color-text-secondary`: `#6B7280` - Secondary text, labels, metadata
- `--color-text-tertiary`: `#9CA3AF` - Disabled text, placeholders
- `--color-text-inverse`: `#FFFFFF` - Text on dark backgrounds

**Primary (Moss Green):**
- `--color-primary`: `#214235` - Primary actions, links, brand elements
- `--color-primary-light`: `#6BA38A` - Hover states, accents
- `--color-primary-lighter`: `#A8D5C4` - Subtle backgrounds, borders
- `--color-primary-dark`: `#1F3D32` - Darker variant for contrast

**Secondary (Blue):**
- `--color-secondary`: `#3B82F6` - Secondary actions, info states
- `--color-secondary-light`: `#60A5FA` - Hover states
- `--color-secondary-lighter`: `#DBEAFE` - Subtle backgrounds

**Status Colors:**
- `--color-success`: `#10B981` - Success states, completed jobs
- `--color-success-light`: `#D1FAE5` - Success backgrounds
- `--color-warning`: `#F59E0B` - Warning states, partial success
- `--color-warning-light`: `#FEF3C7` - Warning backgrounds
- `--color-error`: `#EF4444` - Error states, failed jobs
- `--color-error-light`: `#FEE2E2` - Error backgrounds
- `--color-info`: `#3B82F6` - Info states, running jobs
- `--color-info-light`: `#DBEAFE` - Info backgrounds

**Neutral Grays (Tailwind-inspired):**
- `--color-gray-50`: `#F9FAFB`
- `--color-gray-100`: `#F3F4F6`
- `--color-gray-200`: `#E5E7EB`
- `--color-gray-300`: `#D1D5DB`
- `--color-gray-400`: `#9CA3AF`
- `--color-gray-500`: `#6B7280`
- `--color-gray-600`: `#4B5563`
- `--color-gray-700`: `#374151`
- `--color-gray-800`: `#1F2937`
- `--color-gray-900`: `#111827`

**Borders:**
- `--color-border`: `#E5E7EB` - Default borders
- `--color-border-light`: `#F3F4F6` - Subtle borders
- `--color-border-dark`: `#D1D5DB` - Stronger borders

### Color Usage Guidelines

**Primary (Moss Green) - Brand & Actions:**
- Moss green (`--color-primary` #214235) is the main brand color and primary action color.
- Use for:
  - Primary buttons and CTAs
  - Brand logo and navigation links
  - Active states and focus indicators
  - Primary interactive elements
- This is the signature color that identifies Arandu.

**Secondary (Blue) - Informational Only:**
- Blue (`--color-secondary` #3B82F6) is reserved for "informational" elements only.
- Use for:
  - Info states and status indicators (e.g., "running" jobs)
  - Informational links (not primary actions)
  - Minor accents and secondary information
- Do NOT use blue for primary calls to action or main brand elements.

**Status Colors:**
- Use status colors (success, warning, error, info) for their specific semantic meanings.
- Info color happens to match secondary blue, reinforcing its informational role.

### CSS Variables (Developer-friendly)

```css
:root {
  /* Backgrounds */
  --color-bg-primary: #F9FAFB;
  --color-bg-secondary: #FFFFFF;
  --color-bg-tertiary: #F3F4F6;
  
  /* Text */
  --color-text-primary: #111827;
  --color-text-secondary: #6B7280;
  --color-text-tertiary: #9CA3AF;
  --color-text-inverse: #FFFFFF;
  
  /* Primary (Moss Green) */
  --color-primary: #214235;
  --color-primary-light: #6BA38A;
  --color-primary-lighter: #A8D5C4;
  --color-primary-dark: #1F3D32;
  
  /* Secondary (Blue) */
  --color-secondary: #3B82F6;
  --color-secondary-light: #60A5FA;
  --color-secondary-lighter: #DBEAFE;
  
  /* Status */
  --color-success: #10B981;
  --color-success-light: #D1FAE5;
  --color-warning: #F59E0B;
  --color-warning-light: #FEF3C7;
  --color-error: #EF4444;
  --color-error-light: #FEE2E2;
  --color-info: #3B82F6;
  --color-info-light: #DBEAFE;
  
  /* Borders */
  --color-border: #E5E7EB;
  --color-border-light: #F3F4F6;
  --color-border-dark: #D1D5DB;
}
```

---

## 3. Typography

### Font Families

**Primary:** Inter (sans-serif)
- Modern, clean, highly readable
- Excellent for UI and body text
- Fallback: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`

**Usage:**
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

**Alternative (if Inter not available):**
- IBM Plex Sans
- Source Sans 3

### Type Scale

**H1 - Page Title:**
- Size: `2.25rem` (36px)
- Weight: `600` (semi-bold)
- Line height: `1.2`
- Letter spacing: `-0.02em`
- Color: `--color-text-primary`

**H2 - Section Title:**
- Size: `1.875rem` (30px)
- Weight: `600`
- Line height: `1.3`
- Letter spacing: `-0.01em`
- Color: `--color-text-primary`

**H3 - Subsection Title:**
- Size: `1.5rem` (24px)
- Weight: `600`
- Line height: `1.4`
- Color: `--color-text-primary`

**H4 - Card Title / Small Heading:**
- Size: `1.25rem` (20px)
- Weight: `600`
- Line height: `1.4`
- Color: `--color-text-primary`

**Body - Default Text:**
- Size: `1rem` (16px)
- Weight: `400` (regular)
- Line height: `1.6`
- Color: `--color-text-primary`

**Body Small:**
- Size: `0.875rem` (14px)
- Weight: `400`
- Line height: `1.5`
- Color: `--color-text-secondary`

**Small / Caption:**
- Size: `0.75rem` (12px)
- Weight: `400`
- Line height: `1.4`
- Color: `--color-text-secondary`

**Monospace (for code/logs):**
- Font: `'JetBrains Mono', 'Fira Code', 'Consolas', monospace`
- Size: `0.875rem` (14px)
- Line height: `1.6`
- Background: `--color-bg-tertiary`
- Padding: `0.25rem 0.5rem`
- Border radius: `0.25rem`

### Typography CSS Variables

```css
:root {
  /* Font families */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  
  /* Font sizes */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
  
  /* Font weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  
  /* Line heights */
  --leading-tight: 1.2;
  --leading-snug: 1.3;
  --leading-normal: 1.5;
  --leading-relaxed: 1.6;
}
```

---

## 4. Spacing & Layout

### Spacing Scale

Based on 4px base unit (Tailwind-inspired):

- `--space-1`: `0.25rem` (4px)
- `--space-2`: `0.5rem` (8px)
- `--space-3`: `0.75rem` (12px)
- `--space-4`: `1rem` (16px)
- `--space-5`: `1.25rem` (20px)
- `--space-6`: `1.5rem` (24px)
- `--space-8`: `2rem` (32px)
- `--space-10`: `2.5rem` (40px)
- `--space-12`: `3rem` (48px)
- `--space-16`: `4rem` (64px)
- `--space-20`: `5rem` (80px)
- `--space-24`: `6rem` (96px)

### Layout Rules

**Container:**
- Max width: `1280px` (desktop)
- Padding: `--space-6` (24px) on mobile, `--space-8` (32px) on desktop
- Centered with auto margins

**Grid:**
- Use CSS Grid or Flexbox for layouts
- Gap between grid items: `--space-6` (24px) default
- Responsive breakpoints:
  - Mobile: `< 640px`
  - Tablet: `640px - 1024px`
  - Desktop: `> 1024px`

**Whitespace:**
- Generous padding in cards: `--space-6` (24px)
- Section spacing: `--space-12` (48px) between major sections
- Tight spacing: `--space-2` (8px) for related elements
- Loose spacing: `--space-8` (32px) for separated elements

### Border Radius

**Default:** `--radius-md` (8px) is the standard border radius for most UI objects:
- Cards
- Buttons
- Inputs
- Default interactive elements

**Specific Cases:**
- `--radius-sm`: `0.25rem` (4px) - Small elements, code blocks
- `--radius-lg`: `0.75rem` (12px) - Reserved for modals and very large cards
- `--radius-full`: `9999px` - Reserved for pill-shaped elements (badges, chips)

**Design Principle:** Keep it minimal and lab-like. Most elements use the same, modest radius for consistency.

### Shadows

**Default:** `--shadow-sm` is the default shadow for cards and elevated elements, creating a subtle, minimal elevation that fits the lab-like aesthetic.

**Shadow Scale:**
- `--shadow-sm`: `0 1px 2px 0 rgba(0, 0, 0, 0.05)` - **Default for cards** (subtle elevation)
- `--shadow-md`: `0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)` - Use sparingly (overlays, prominent cards)
- `--shadow-lg`: `0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)` - Rare use (very prominent elements, modals)
- `--shadow-none`: `none` - No shadow

**Design Principle:** Stronger shadows (`--shadow-md` / `--shadow-lg`) should be used sparingly. Most UI elements should have minimal or no shadow to maintain the clean, lab-like feel.

---

## 5. Core Components

### 5.1 Buttons

**Primary Button:**
- Background: `--color-primary` (#214235)
- Text: `--color-text-inverse` (white)
- Padding: `--space-3` (12px) `--space-4` (16px)
- Border radius: `--radius-md` (8px)
- Font weight: `--font-medium` (500)
- Hover: Background `--color-primary-dark` (#1F3D32)
- Active: Slight scale down (0.98)
- Disabled: Opacity `0.5`, cursor `not-allowed`

**Secondary Button:**
- Background: `transparent`
- Border: `1px solid --color-border-dark`
- Text: `--color-text-primary`
- Padding: Same as primary
- Hover: Background `--color-bg-tertiary`
- Active: Same as primary

**Subtle Button:**
- Background: `transparent`
- Border: `none`
- Text: `--color-text-secondary`
- Padding: `--space-2` (8px) `--space-3` (12px)
- Hover: Background `--color-bg-tertiary`, text `--color-text-primary`

**Button Sizes:**
- Small: `--space-2` (8px) `--space-3` (12px), `--text-sm`
- Medium (default): `--space-3` (12px) `--space-4` (16px), `--text-base`
- Large: `--space-4` (16px) `--space-6` (24px), `--text-lg`

### 5.2 Cards

**Default Card:**
- Background: `--color-bg-secondary` (white)
- Border: `1px solid --color-border`
- Border radius: `--radius-md` (8px) - Default radius
- Padding: `--space-6` (24px)
- Shadow: `--shadow-sm` - Default subtle shadow
- Hover (if interactive): Shadow `--shadow-md`, slight lift

**Card Header:**
- Border bottom: `1px solid --color-border-light`
- Padding bottom: `--space-4` (16px)
- Margin bottom: `--space-4` (16px)

**Card Footer:**
- Border top: `1px solid --color-border-light`
- Padding top: `--space-4` (16px)
- Margin top: `--space-4` (16px)

### 5.3 Status Badges

**Design:**
- Display: `inline-flex`
- Padding: `--space-1` (4px) `--space-2` (8px)
- Border radius: `--radius-full` (pill shape)
- Font size: `--text-xs` (12px)
- Font weight: `--font-medium` (500)
- Text transform: `uppercase`
- Letter spacing: `0.05em`

**Status Variants:**

**Pending:**
- Background: `--color-gray-100`
- Text: `--color-gray-700`
- Icon: Clock/spinner

**Running:**
- Background: `--color-info-light` (#DBEAFE)
- Text: `--color-info` (#3B82F6)
- Icon: Spinner (animated)

**Success / Completed:**
- Background: `--color-success-light` (#D1FAE5)
- Text: `--color-success` (#10B981)
- Icon: Checkmark

**Partial:**
- Background: `--color-warning-light` (#FEF3C7)
- Text: `--color-warning` (#F59E0B)
- Icon: Warning/exclamation

**Failed:**
- Background: `--color-error-light` (#FEE2E2)
- Text: `--color-error` (#EF4444)
- Icon: X/error

### 5.4 Navigation Bar

**Structure:**
- Background: `--color-bg-secondary` (white)
- Border bottom: `1px solid --color-border`
- Height: `64px`
- Padding: `0 --space-6` (24px)
- Display: `flex`, `align-items: center`, `justify-content: space-between`

**Logo/Brand:**
- Font size: `--text-xl` (20px)
- Font weight: `--font-semibold` (600)
- Color: `--color-primary` (#214235)

**Links:**
- Display: `flex`, gap `--space-6` (24px)
- Font size: `--text-base`
- Color: `--color-text-secondary`
- Hover: Color `--color-primary`
- Active: Color `--color-primary`, font weight `--font-medium`

### 5.5 Tables / Lists

**Table:**
- Width: `100%`
- Border collapse: `separate`
- Border spacing: `0`
- Background: `--color-bg-secondary` (white)
- Border: `1px solid --color-border`
- Border radius: `--radius-md` (8px)
- Overflow: `hidden`

**Table Header:**
- Background: `--color-bg-tertiary` (#F3F4F6)
- Padding: `--space-3` (12px) `--space-4` (16px)
- Font weight: `--font-semibold` (600)
- Font size: `--text-sm` (14px)
- Text transform: `uppercase`
- Letter spacing: `0.05em`
- Color: `--color-text-secondary`

**Table Row:**
- Border bottom: `1px solid --color-border-light`
- Padding: `--space-4` (16px)
- Hover: Background `--color-bg-tertiary`

**Table Cell:**
- Padding: `--space-3` (12px) `--space-4` (16px)
- Vertical align: `middle`

**List (Alternative to Table):**
- Display: `flex`, `flex-direction: column`
- Gap: `--space-2` (8px)
- Each item: Card-like with padding `--space-4` (16px)

### 5.6 Form Inputs

**Text Input:**
- Background: `--color-bg-secondary` (white)
- Border: `1px solid --color-border`
- Border radius: `--radius-md` (8px)
- Padding: `--space-3` (12px) `--space-4` (16px)
- Font size: `--text-base`
- Focus: Border color `--color-primary`, outline `2px solid --color-primary-lighter`
- Disabled: Background `--color-bg-tertiary`, opacity `0.6`

**Textarea:**
- Same as text input
- Min height: `120px`
- Resize: `vertical`

**Label:**
- Font size: `--text-sm` (14px)
- Font weight: `--font-medium` (500)
- Color: `--color-text-primary`
- Margin bottom: `--space-2` (8px)
- Display: `block`

### 5.7 Log Viewer

**Purpose:** Display experiment logs (stdout/stderr) in the Job Detail page. This is a first-class component for showing execution output.

**Design:**
- **Container:**
  - Background: `--color-bg-secondary` (white) or `--color-bg-tertiary` (#F3F4F6) for subtle distinction
  - Border: `1px solid --color-border`
  - Border radius: `--radius-md` (8px)
  - Padding: `--space-4` (16px)
  - Max height: `400px` (or configurable)
  - Overflow: `auto` (scrollable)

- **Log Content:**
  - Font: Monospace (`--font-mono`)
  - Font size: `--text-sm` (14px)
  - Line height: `--leading-relaxed` (1.6)
  - Color: `--color-text-primary`
  - White space: `pre-wrap` (preserve formatting, wrap long lines)
  - Background: Transparent or very subtle `--color-bg-tertiary`

- **Visual Distinction:**
  - If showing both system logs and experiment logs:
    - System logs: Subtle background tint or left border indicator
    - Experiment logs: Default styling
  - Consider line numbers (optional, for long logs)

- **Actions:**
  - "Download Full Logs" button: Secondary button style, positioned above or below log viewer
  - "Copy Snippet" button (optional): Subtle button, appears on hover or as icon button next to log viewer
  - Auto-scroll to bottom toggle (optional, for streaming logs)

**Behavior:**
- Handle long content gracefully without overwhelming the page
- Truncate very long logs with "Show more" option if needed (though full logs should be downloadable)
- Support syntax highlighting for error messages (optional)
- Smooth scrolling for auto-refresh scenarios

### 5.8 Utility Micro-Components

#### CopyToClipboard

**Purpose:** Small icon/button for copying text snippets (badge snippets, log snippets, commands).

**Design:**
- **Style:** Subtle, minimal
- **Size:** Small icon button (approximately 32x32px)
- **Appearance:**
  - Icon: Copy/clipboard icon (SVG, ~16px)
  - Background: Transparent or `--color-bg-tertiary` on hover
  - Border: None or very subtle
  - Border radius: `--radius-sm` (4px)
  - Padding: `--space-2` (8px)
- **Placement:** Appears next to code/log blocks, badge snippets, or inline with copyable content
- **States:**
  - Default: Subtle gray icon
  - Hover: Background `--color-bg-tertiary`, icon color `--color-text-primary`
  - Active/Clicked: Brief visual feedback (checkmark icon, color change to `--color-success`)
- **Accessibility:** ARIA label "Copy to clipboard"

#### Meta Tag / Chip

**Purpose:** Display metadata such as language ("Python only"), environment type detected ("pip", "conda"), created time ("2 hours ago").

**Design:**
- **Style:** Pill-shaped, small text
- **Appearance:**
  - Background: `--color-bg-tertiary` (#F3F4F6) or very light tint of primary/secondary
  - Text: `--color-text-secondary` (#6B7280)
  - Font size: `--text-xs` (12px)
  - Font weight: `--font-medium` (500)
  - Padding: `--space-1` (4px) `--space-2` (8px)
  - Border radius: `--radius-full` (pill shape)
  - Border: None or very subtle `1px solid --color-border-light`
- **Variants:**
  - **Neutral:** Default gray background (for timestamps, generic metadata)
  - **Tinted:** Light tint of primary or secondary color (for environment type, language)
- **Usage:** Inline with text, or grouped in a flex container with small gap

**Examples:**
- `[Python only]` - Light green tint
- `[pip]` - Light blue tint
- `[2 hours ago]` - Neutral gray
- `[conda]` - Light blue tint

---

## 6. Key Screens

### 6.1 Home / Landing Page

**Layout:**
```
┌─────────────────────────────────────────┐
│  [Nav Bar: Logo | Jobs | About]        │
├─────────────────────────────────────────┤
│                                         │
│  [Hero Section - Centered]              │
│  ┌─────────────────────────────────┐   │
│  │  H1: Arandu Repro               │   │
│  │  Body: Reproduce AI research... │   │
│  │                                 │   │
│  │  [Job Submission Form Card]    │   │
│  │  ┌─────────────────────────┐  │   │
│  │  │ Repo URL * [input]       │  │   │
│  │  │ arXiv ID  [input]         │  │   │
│  │  │ Run Command [input]       │  │   │
│  │  │                           │  │   │
│  │  │ [Submit Button - Primary] │  │   │
│  │  └─────────────────────────┘  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Features Section - 3 columns]        │
│  ┌──────┐ ┌──────┐ ┌──────┐          │
│  │ Icon │ │ Icon │ │ Icon │          │
│  │ Title│ │ Title│ │ Title│          │
│  │ Text │ │ Text │ │ Text │          │
│  └──────┘ └──────┘ └──────┘          │
│                                         │
└─────────────────────────────────────────┘
```

**Elements:**
- Nav bar at top (fixed or static)
- Hero section with centered form card
- Form: Repo URL (required), arXiv ID (optional), Run Command (optional)
- Submit button (primary, full width in form)
- Features section below (optional, for landing page)

### 6.2 Jobs Overview / List

**Layout:**
```
┌─────────────────────────────────────────┐
│  [Nav Bar]                             │
├─────────────────────────────────────────┤
│  H1: Jobs                              │
│  [Filter: All | Pending | Running |    │
│           Completed | Failed]          │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ [Job Card]                      │   │
│  │ ┌─────────────────────────────┐ │   │
│  │ │ Repo: github.com/user/repo  │ │   │
│  │ │ Status: [Running Badge]      │ │   │
│  │ │ Created: 2 hours ago         │ │   │
│  │ │                              │ │   │
│  │ │ [View Details Button]      │ │   │
│  │ └─────────────────────────────┘ │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ [Job Card]                      │   │
│  │ ... (same structure)           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Pagination or "Load More"]           │
└─────────────────────────────────────────┘
```

**Elements:**
- Page title (H1)
- Filter tabs or dropdown (status filter)
- List of job cards (or table view toggle)
- Each card: Repo URL, status badge, timestamp, action button
- Pagination or infinite scroll

**Alternative Table View:**
- Table with columns: Repo URL, Status, Created, Actions
- Sortable columns
- Click row to view details

### 6.3 Job Detail Page

**Layout:**
```
┌─────────────────────────────────────────┐
│  [Nav Bar]                             │
├─────────────────────────────────────────┤
│  [Breadcrumb: Jobs > Job #abc123]     │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ [Job Info Card]                 │   │
│  │ Repo: github.com/user/repo      │   │
│  │ Status: [Completed Badge]        │   │
│  │ Created: 2024-01-15 10:30        │   │
│  │ Duration: 5m 23s                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ H2: Execution Logs              │   │
│  │ ┌─────────────────────────────┐│   │
│  │ │ [Monospace log output]       ││   │
│  │ │ (scrollable, max-height)     ││   │
│  │ │                               ││   │
│  │ └─────────────────────────────┘│   │
│  │ [Download Full Logs Button]     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ H2: Artifacts                   │   │
│  │ ┌──────┐ ┌──────┐ ┌──────┐    │   │
│  │ │Report│ │Note- │ │Badge │    │   │
│  │ │[Down]│ │book  │ │[Copy]│    │   │
│  │ │      │ │[Down]│ │      │    │   │
│  │ └──────┘ └──────┘ └──────┘    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ H2: Badge Snippet               │   │
│  │ [Code block with copy button]   │   │
│  │ [![Reproducible](...)](...)     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Auto-refresh indicator if running]   │
└─────────────────────────────────────────┘
```

**Elements:**
- Breadcrumb navigation
- Job info card (metadata, status, timestamps)
- Execution logs section (monospace, scrollable, max height ~400px)
- Artifacts section (download buttons for report, notebook, badge)
- Badge snippet section (code block with copy button)
- Auto-refresh indicator if status is pending/running
- Error message display if failed

**Status-specific content:**
- **Pending/Running:** Show spinner, auto-refresh, "Processing..." message
- **Completed:** Show all artifacts, success message
- **Failed:** Show error message prominently, truncated logs, no artifacts

---

## 7. Implementation Notes

### CSS Framework Decision

**Arandu Repro v0 uses Next.js + Tailwind CSS.**

**Implementation:**
- Tailwind CSS will be configured with custom design tokens (colors, spacing, radius, shadows) matching this design system
- Configure `tailwind.config.js` to extend Tailwind's default theme with our custom tokens
- Use Tailwind utility classes for rapid development and consistency
- Custom components can use Tailwind's `@apply` directive or component classes

**Customization:**
- All design tokens (colors, spacing, typography, radius, shadows) should be mapped to Tailwind config
- CSS variables can still be used for dynamic theming if needed
- Tailwind's JIT mode for optimal bundle size

**Note:** CSS Modules or styled-components can be used later for special cases or complex components, but are not the default in v0. The primary approach is Tailwind CSS utility classes.

### Responsive Design

**Mobile-first approach:**
- Stack form fields vertically on mobile
- Cards full-width on mobile, grid on desktop
- Navigation: hamburger menu on mobile, horizontal on desktop
- Tables: Switch to card list on mobile

**Breakpoints:**
- Mobile: `< 640px`
- Tablet: `640px - 1024px`
- Desktop: `> 1024px`

### Accessibility

- Ensure color contrast ratios meet WCAG AA (4.5:1 for normal text, 3:1 for large text)
- Use semantic HTML (`<nav>`, `<main>`, `<article>`, etc.)
- Keyboard navigation support
- Focus indicators visible (use `--color-primary` for focus rings)
- ARIA labels for status badges and interactive elements

### Animation & Transitions

**Subtle animations:**
- Button hover: `transition: all 0.2s ease`
- Card hover: `transition: box-shadow 0.2s ease`
- Status badge updates: Fade in (`opacity: 0 → 1`)
- Loading spinner: Smooth rotation

**Avoid:**
- Heavy animations that distract
- Auto-playing animations
- Excessive motion (respect `prefers-reduced-motion`)

---

This design system provides a complete, implementable foundation for Arandu Repro v0's UI. All tokens are defined in developer-friendly formats (CSS variables), and components are described with enough detail for implementation in Next.js or any modern frontend framework.

