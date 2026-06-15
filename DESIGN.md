# Medelite Facility Assessment Design Notes

This project follows the case-study brief, the supplied report snapshot, the
official Infinite/Medelite logo asset, and the Google `design.md` principle of
making product decisions explicit in the repository.

## Product Goal

Build a small but production-shaped internal tool that helps Medelite evaluate
skilled nursing facilities before outreach or partnership conversations.

The app must do four jobs well:

1. Fetch live CMS facility data by CCN.
2. Combine public data with internal manual operational inputs.
3. Explain facility performance through cards, charts, and QA warnings.
4. Export a polished PDF and editable DOCX report.

## Experience Principles

- Make the working report generator the first screen. No marketing landing page.
- Keep the interface operational and scan-friendly: dense, calm, and accurate.
- Treat the PDF report preview as a first-class artifact, not an afterthought.
- Surface data freshness, missing values, and source links visibly.
- Preserve the branding guardrail: `INFINITE` is static platform branding and
  never becomes the facility name.

## Visual System

- Background: `#f8fafc`
- Primary: `#1e40af`
- Secondary: `#3b82f6`
- Accent: `#d97706`
- Ink: `#0f172a`
- Muted ink: `#64748b`
- Border: `#dbeafe`
- Success: `#15803d`
- Warning: `#b45309`
- Danger: `#dc2626`

Typography uses system fonts with an analytics-product feel:

- Headings: `Inter`, `Segoe UI`, sans-serif
- Body: `Inter`, `Segoe UI`, sans-serif
- Numeric labels: tabular figures

## Layout

Desktop:

- Sticky header with logo, workflow status, and export actions.
- Two-column workbench:
  - left rail for CCN lookup and manual inputs
  - main panel for CMS summary, charts, opportunity score, and report preview

Mobile:

- Header stacks compactly.
- Manual inputs move above analytics.
- Cards and charts become single-column.
- Export actions remain reachable after a successful assessment.

## Chart Rules

- Compare Facility vs State vs National for the four hospitalization/ED measures.
- Use grouped bars for direct comparison.
- Use labels and tooltips; do not rely on color alone.
- Keep units explicit:
  - STR measures are percentages.
  - LT measures are rates per 1,000 long-stay resident days.

## Data Assumptions

- CMS data is live and may differ from the static sample PDF.
- CCNs are strings, not numbers, to preserve leading zeros.
- Server-side CMS fetching avoids CORS and makes retry/caching behavior explicit.
- BigQuery logging is optional and must never block report generation.

