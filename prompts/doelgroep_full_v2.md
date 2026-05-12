# Doelgroep Full Report — V2

Long-form companion to `doelgroep_distill.md`. Used by
`templates/doelgroep_web.html` on `doelgroepenrapport.nl` for converted leads.

## TODO before go-live

Drop the production V2 long-form prompt here. Output schema extends the
distill output with:

```json
{
  "market_narrative": "string — 200-300 words",
  "persona_segments": [
    { "name": "...", "size_pct": 0, "drivers": ["..."], "channels": ["..."] }
  ],
  "channel_strategy": { "primary": "...", "secondary": ["..."] },
  "salary_benchmark_table": [
    { "region": "...", "p25": 0, "median": 0, "p75": 0 }
  ],
  "appendix": { "...": "..." }
}
```
