# ACTIE ITEMS WOUTER

**DEADLINE:** 17 MEI 2026 08:00 CET (Go-live)

## PRIORITEIT 1: GitHub (ASAP)

- [ ] **1. Push lokale repo naar GitHub**
  ```bash
  cd /home/claude/projects/jobdigger-email-automation/
  git push -u origin main
  ```
  Verifieer: https://github.com/WouterArtsRecruitin/recruitin-jobdigger-v3

- [ ] **2. Voeg 7 GitHub Actions geheimen toe**
  - `ANTHROPIC_API_KEY` (je Anthropic console)
  - `LEMLIST_API_KEY` (1d1709e871748ecaf06df5309992efc6)
  - `SUPABASE_URL` (je Supabase project)
  - `SUPABASE_KEY` (Supabase service key)
  - `SLACK_WEBHOOK_URL` (optioneel)

- [ ] **3. Schakel GitHub Actions in** (Settings → Actions → General)

## PRIORITEIT 2: Externe Services (16 mei)

- [ ] **4. Setup Supabase** — Bucket: `jobdigger-pdfs`, Openbare lezing
- [ ] **5. Verifieer Lemlist** — Campagne: "JobDigger P12", 5 touches × 14 dagen
- [ ] **6. Setup Slack** (optioneel) — Webhook voor meldingen

## PRIORITEIT 3: Test (16 mei 14:00)

- [ ] **7. Voer testworkflow uit** — Actions → "Workflow uitvoeren"
  ```
  ✓ 200 vacatures geladen
  ✓ ICP gekwalificeerd: 20/200
  ✓ 20 leads verwerkt, 0 fouten
  ```
- [ ] **8. Verifieer Supabase PDF's** (~40 bestanden)
- [ ] **9. Verifieer Lemlist contacten** (20 nieuw)

## PRIORITEIT 4: Pre-Live (17 mei 07:00)

- [ ] **10. Eindchecklist** — Alle 7 geheimen, Actions ingeschakeld, test OK
- [ ] **11. Stel `LEAD_BATCH_SIZE = 20` in** + laatste git push

## GO-LIVE (17 mei 08:00 CET)
- ✓ Automatische uitvoering om 07:00 UTC
- ✓ 20 leads, 40 PDF's, 0 fouten verwacht

## Kosten

| Metriek | Waarde |
|---------|--------|
| Per dag | €3,07 |
| Per maand | €92,10 |
| ROI | 6-19x |