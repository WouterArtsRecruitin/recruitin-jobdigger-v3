# JobDigger V3

Automated recruitment funnel: scrape → ICP-filter → distill via Claude → render PDF reports → upload to Lemlist.

Runs daily at **07:00 UTC (08:00 CET)** via GitHub Actions.

## Pipeline

```
data/daily_vacancies.json   (from external scraper)
        │
        ▼
ICPFilter (6 binary gates)        →  ~20 qualified leads
        │
        ▼
PromptExecutor (Claude Opus)      →  vacature + doelgroep distills
        │
        ▼
PDFGenerator (WeasyPrint)         →  2 PDFs per lead (Touch 1 + Touch 2)
        │
        ▼
StorageManager (Supabase)         →  public URLs
        │
        ▼
LemlistUploader                   →  contacts added to 5-touch campaign
```

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in secrets
```

WeasyPrint needs system libs on Linux:

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0
```

## Run

```bash
# End-to-end test with one dummy lead
python test_full_pipeline.py

# Full daily run (reads data/daily_vacancies.json)
python scripts/daily_automation.py
```

## Configuration

All knobs are environment variables — see `.env.example`. Key ones:

| Variable           | Default                    | Purpose                                     |
|--------------------|----------------------------|---------------------------------------------|
| `CLAUDE_MODEL`     | `claude-opus-4-7`          | Model for distills                          |
| `LEAD_BATCH_SIZE`  | `20`                       | Max qualified leads per run                 |
| `SUPABASE_BUCKET`  | `jobdigger-pdfs`           | Bucket for rendered PDFs (public read)      |

## Layout

```
.github/workflows/daily-cron.yml   GitHub Actions schedule
prompts/                           Claude system prompts (markdown)
templates/                         Jinja2 HTML → WeasyPrint PDF + web pages
scripts/daily_automation.py        Main orchestrator
test_full_pipeline.py              Single-lead smoke test
data/daily_vacancies.json          Scraper output (gitignored)
storage/pdfs/                      Local PDF cache (gitignored)
logs/                              Run logs (gitignored)
```

## Deployment

See `DEPLOYMENT_CHECKLIST.md`.
