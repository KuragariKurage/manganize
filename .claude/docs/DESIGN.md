# DESIGN

## Overview

Manga revision UX is being upgraded to improve annotation visibility, reduce scroll-heavy input, and enable direct before/after comparison.

## Architecture

- Keep existing revision backend APIs and generation pipeline.
- Introduce a dedicated revision workspace page for editing and comparison.
- Move per-target instruction input from list-based form to inline tooltip editing on canvas.

## Implementation Plan

### Patterns

- Canvas overlay for point/box annotation rendering.
- Single active tooltip editor bound to selected target.
- Stateful compare panel (`idle`, `processing`, `completed`, `error`) on the same screen.

### Libraries

- Keep existing FastAPI + Jinja2 + HTMX + vanilla JS stack.
- No new frontend framework is introduced for this change.

### Key Decisions

- Orange is the canonical marker color for rectangles and index badges.
- Target indices are rendered as orange circular badges with white text and larger sizing.
- Selecting a region immediately opens inline input near that region.
- Only one tooltip can be open at a time; switching targets closes the previous tooltip.
- If switching with unsaved changes, show `Save & Switch / Discard & Switch` confirmation.
- Keep a persistent edit summary panel for reviewing and reopening past edits.
- Revision editing is moved to a separate workspace page with side-by-side before/after comparison.
- On mobile, tooltip overflow falls back to a bottom-fixed panel.

## TODO

- Implement workspace route and template.
- Replace list-first input flow with tooltip-first flow.
- Add persistent edit summary panel and selection sync with canvas markers.
- Add UI tests for marker visibility and compare-state transitions.

## Open Questions

- None currently.

## Changelog

- 2026-02-08: Recorded revision UX enhancement decisions (orange markers, inline tooltip input, dedicated comparison workspace).
- 2026-02-09: Finalized tooltip-singleton behavior, unsaved-switch confirmation, persistent edit summary panel, and mobile bottom-panel fallback.
- 2026-02-09: Removed coordinate text from canvas UI; keep marker outlines and index badges only.
