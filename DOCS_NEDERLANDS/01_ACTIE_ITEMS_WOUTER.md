# 🚀 ACTIE ITEMS WOUTER — JobDigger V3 Fase 5

**DEADLINE:** 17 MEI 2026 08:00 CET (Go-live)

## PRIORITEIT 1: GitHub (ASAP)

- [ ] **1. Push lokale repo naar GitHub**
  ```bash
  cd /path/to/jobdigger-email-automation/
  git push -u origin main
  ```

- [ ] **2. Voeg 7 GitHub Actions geheimen toe**
  - `ANTHROPIC_API_KEY`
  - `LEMLIST_API_KEY` (1d1709e871748ecaf06df5309992efc6)
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `SLACK_WEBHOOK_URL`
  - `SLACK_CHANNEL_ID`
  - `LEAD_BATCH_SIZE` (test: 5, live: 20)

- [ ] **3. Schakel GitHub Actions in**

## PRIORITEIT 2: Services (16 mei)

- [ ] **4. Setup Supabase** — Bucket `jobdigger-pdfs`
- [ ] **5. Verifieer Lemlist** — Campagne "JobDigger P12"
- [ ] **6. Setup Slack** (optioneel)

## PRIORITEIT 3: Test (16 mei 14:00)

- [ ] **7. Test workflow** — Actions → Workflow uitvoeren
- [ ] **8. Verifieer Supabase PDF's** (~40 bestanden)
- [ ] **9. Verifieer Lemlist contacten** (20 nieuw)

## PRIORITEIT 4: Pre-Live (17 mei 07:00)

- [ ] **10. Eindchecklist** — Alle geheimen + Actions OK
- [ ] **11. Set LEAD_BATCH_SIZE = 20**

## GO-LIVE (17 mei 08:00 CET)
✓ Automatische start | ✓ 20 leads/dag | ✓ 0 fouten

---

**Kosten:** €92,10/maand | **ROI:** 6-19x | **Inkomsten:** €600-1.800