# Arandu CoReview Studio - Frontend

Next.js 14 frontend for the Review MVP.

## Setup

```bash
npm install
npm run dev
```

## Pages

- `/` - Home page
- `/reviews/submit` - Submit a review
- `/reviews/[id]` - Review detail page with tabs

## Components

- `ClaimCard` - Display and edit claims
- `ChecklistPanel` - Method checklist table
- `ScorePanel` - Quality score display
- `NarrationDrawer` - Score explanation modal
- `ArtifactsPanel` - Download artifacts and badges
- `BadgeTile` - Badge preview and snippet

## Design System

Uses Tailwind CSS with custom design tokens matching `DESIGN_SYSTEM_V0.md`:
- Primary color: Moss Green (#214235)
- Secondary color: Blue (#3B82F6) - Informational only
- Status colors: Success, Warning, Error, Info
- Typography: Inter font family
- Spacing: 4px base unit
- Border radius: 8px default
