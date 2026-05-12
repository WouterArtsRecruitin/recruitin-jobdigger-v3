# JobDigger V3 — Deployment Checklist

**Go-live target:** 17 May 2026, 08:00 CET

## 1. GitHub repo

- [x] Repo created: `WouterArtsRecruitin/recruitin-jobdigger-v3`
- [ ] Scaffold PR merged into `main`
- [ ] Branch protection on `main` (require PR + checks)

## 2. GitHub Actions secrets

Settings → Secrets and variables → Actions → **New repository secret**:

| Name                  | Source                                               |
|-----------------------|------------------------------------------------------|
| `ANTHROPIC_API_KEY`   | Anthropic console                                    |
| `LEMLIST_API_KEY`     | Lemlist account settings (never commit to repo)      |
| `LEMLIST_CAMPAIGN_ID` | Lemlist campaign URL (`/campaigns/<id>/...`)         |
| `SUPABASE_URL`        | Supabase project settings → API                      |
| `SUPABASE_KEY`        | Supabase service-role key                            |
| `SLACK_WEBHOOK_URL`   | Slack app incoming-webhook (optional)                |

Optional repository **variables** (not secrets):

| Name              | Default            |
|-------------------|--------------------|
| `CLAUDE_MODEL`    | `claude-opus-4-7`  |
| `SUPABASE_BUCKET` | `jobdigger-pdfs`   |
| `LEAD_BATCH_SIZE` | `20`               |

## 3. External services

### Supabase
- [ ] Create bucket `jobdigger-pdfs`
- [ ] Bucket policy: public read, authenticated write
- [ ] Service-role key copied into `SUPABASE_KEY` secret

### Lemlist
- [ ] API key created and stored in `LEMLIST_API_KEY` secret
- [ ] Campaign created: **"JobDigger P12 — Stage 2 Optimized"**
- [ ] 5 touches configured (Day 0 / 3 / 6 / 10 / 13)
- [ ] Variables `vacaturePdfUrl` and `doelgroepPdfUrl` referenced in templates
- [ ] Campaign ID stored in `LEMLIST_CAMPAIGN_ID` secret

### Scraper
- [ ] V5.2 scraper writes to `data/daily_vacancies.json` before 07:00 UTC
- [ ] Output validated against `ICPFilter` fields (sector, seniority, contact_email, …)

## 4. Test run (16 May, 14:00 CET)

```bash
# Locally
cp .env.example .env  # fill secrets
python test_full_pipeline.py
```

- [ ] Single-lead smoke test renders both PDFs
- [ ] `Actions → JobDigger Daily Automation → Run workflow` (manual trigger)
- [ ] Set `lead_batch_size = 5` input for first dry-run
- [ ] Verify 5 PDFs in Supabase bucket
- [ ] Verify 5 contacts in Lemlist campaign

## 5. Pre-live audit (17 May, 07:00 CET)

- [ ] All 6 secrets configured (Slack optional)
- [ ] Scraper output present and ≥100 vacancies
- [ ] No failing runs in `Actions` history
- [ ] `LEAD_BATCH_SIZE` set to `20` (default, or repo variable)

## 6. Go-live (17 May, 08:00 CET)

- [ ] Cron triggers at 07:00 UTC
- [ ] Slack notification received with success summary
- [ ] Spot-check: 1 PDF opens correctly from Supabase URL
- [ ] Spot-check: 1 Lemlist contact has both PDF URLs populated

## 7. Rollback

```bash
gh workflow disable .github/workflows/daily-cron.yml
# Fix, push, smoke-test
gh workflow enable .github/workflows/daily-cron.yml
```

## Success metrics (first week)

| Metric                       | Target  |
|------------------------------|---------|
| Leads processed / day        | 20      |
| ICP pass rate                | 15-20%  |
| PDF render success           | > 95%   |
| Lemlist upload success       | > 95%   |
| Reply rate (Touch 1-5)       | 8-12%   |
