# ✅ DEPLOYMENT CHECKLIST — Fase 5 Go-Live

**Target:** 17 mei 2026 08:00 CET

---

## ☑️ FASE 4 VOLTOOID
- [x] Orchestrator (`daily_automation.py` — 440 regels)
- [x] GitHub Actions (`daily-cron.yml`)
- [x] Test runner (`test_full_pipeline.py`)
- [x] Git repo geïnitialiseerd + commits
- [x] Nederlandse documentatie

---

## ⏳ FASE 5: DEPLOYMENT SETUP

### **5.1 GitHub Repository** (ASAP)

- [ ] **Push lokale repo:**
  ```bash
  cd /path/to/jobdigger-email-automation/
  git push -u origin main
  ```

- [ ] **Verifieer op GitHub:**
  https://github.com/WouterArtsRecruitin/recruitin-jobdigger-v3

### **5.2 GitHub Actions Geheimen** (ASAP)

Settings → Secrets and variables → Actions

- [ ] `ANTHROPIC_API_KEY` (sk-ant-...)
- [ ] `LEMLIST_API_KEY` (1d1709e871748ecaf06df5309992efc6)
- [ ] `SUPABASE_URL` (https://...supabase.co)
- [ ] `SUPABASE_KEY` (eyJhbGc...)
- [ ] `SLACK_WEBHOOK_URL` (optioneel)
- [ ] `SLACK_CHANNEL_ID` (optioneel)
- [ ] `LEAD_BATCH_SIZE` (test: 5)

### **5.3 GitHub Actions Activering** (ASAP)

Settings → Actions → General → ✅ Toestaan

### **5.4 Supabase Setup** (tot 16 mei)

- [ ] Maak bucket aan: `jobdigger-pdfs`
- [ ] Rechten: Public Read + Auth Write
- [ ] Noteer `SUPABASE_URL` + `SUPABASE_KEY`

### **5.5 Lemlist Campagne** (tot 16 mei)

- [ ] Verifieer API-sleutel ✓
- [ ] Maak campagne aan: "JobDigger P12 - Stage 2"
- [ ] Setup 5 e-mailsequence (14 dagen)
- [ ] Verifieer sending domain

### **5.6 Slack Setup** (optioneel, tot 16 mei)

- [ ] Create incoming webhook
- [ ] Noteer URL + Channel ID

### **5.7 Lokale .env** (voor test)

```
ANTHROPIC_API_KEY=sk-ant-...
LEMLIST_API_KEY=1d1709e871748ecaf06df5309992efc6
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJhbGc...
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SLACK_CHANNEL_ID=C024BE91L
LEAD_BATCH_SIZE=5
```

---

## 🧪 FASE 5.8: TEST RUN (16 mei 14:00)

- [ ] **Trigger workflow:** Actions → "Workflow uitvoeren"

- [ ] **Verify output:**
  ```
  ✓ 200 vacatures geladen
  ✓ ICP gekwalificeerd: 20/200
  ✓ 20 leads verwerkt, 0 fouten
  ✓ PDFs gegenereerd: ~40 bestanden
  ```

- [ ] **Check Supabase:** Bucket `jobdigger-pdfs` → 40 files

- [ ] **Check Lemlist:** 20 nieuwe contacten aangemaakt

---

## 🔍 FASE 5.9: PRE-LIVE AUDIT (17 mei 07:00)

- [ ] Alle 7 geheimen geconfigureerd ✓
- [ ] GitHub Actions ingeschakeld ✓
- [ ] Test run succesvol ✓
- [ ] Supabase PDFs aanwezig ✓
- [ ] Lemlist contacten OK ✓

---

## 🚀 FASE 5.10: GO-LIVE (17 mei 08:00 CET)

- [ ] Stel `LEAD_BATCH_SIZE = 20` in (GitHub Secrets)
- [ ] Laatste git push:
  ```bash
  git add .
  git commit -m "Fase 5: Live configuration"
  git push origin main
  ```

- [ ] Monitor eerste 2 uur:
  ```
  ✓ Automatische start: 07:00 UTC (08:00 CET)
  ✓ 20 leads/dag verwacht
  ✓ 40 PDF's gegenereerd
  ✓ 0 fouten target
  ```

---

## 📊 Succesmetrieken (Week 1)

| Metriek | Target | Waarde |
|---------|--------|--------|
| Leads/dag | 20 | TBD |
| ICP slagingspercentage | 15-20% | TBD |
| PDF render succes | >95% | TBD |
| Antwoordtarief T1 | 8-12% | TBD (week 2) |

---

## 💰 Maandelijkse Kosten

| Service | Bedrag |
|---------|--------|
| Claude API (Opus) | €27,60 |
| Lemlist | €60,00 |
| Supabase | €4,50 |
| **TOTAAL** | **€92,10** |

**Verwachte inkomsten:** €600-1.800/maand | **ROI:** 6-19x

---

## 🚨 Terugdraaiing

Als iets fout gaat:

```bash
gh workflow disable daily-cron.yml
python test_full_pipeline.py  # Fix + verify
gh workflow enable daily-cron.yml
```

---

## ✅ Checklist voltooid?

- [ ] Alles afgevinkt
- [ ] Go-live gepland
- [ ] Iemand is assigned

**Status:** ⏳ Wacht op jouw actie