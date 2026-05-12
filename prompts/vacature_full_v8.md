# Vacature Full Report — V8

Long-form companion to `vacature_distill.md`. Used to render the **full**
report (12-15 pages) when a lead converts via Touch 1-2 PDF teasers.

Out of scope for the daily Lemlist drip. Wired up later in the web flow
(`templates/vacatura_web.html` → `kandidatentekort.nl`).

## TODO before go-live

Drop the production V8 long-form prompt here. The downstream renderer
expects the same root-level keys as the distill output, with the addition of:

```json
{
  "executive_summary": "string — 200-300 words",
  "deep_dive": {
    "...": "..."
  },
  "action_plan": ["..."],
  "appendix": { "...": "..." }
}
```
