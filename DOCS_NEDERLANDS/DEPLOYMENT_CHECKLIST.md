# DEPLOYMENT CHECKLIST

## ✅ FASE 4 VOLTOOID
- [x] Orchestrator (`daily_automation.py`)
- [x] GitHub Actions (`daily-cron.yml`)
- [x] Test runner (`test_full_pipeline.py`)
- [x] Git repo geïnitialiseerd

## ⏳ FASE 5: GO-LIVE SETUP

### 5.1 GitHub repository
- [ ] Push: `git push -u origin main`

### 5.2 Geheimen (7 variabelen)
```
ANTHROPIC_API_KEY, LEMLIST_API_KEY, SUPABASE_URL, 
SUPABASE_KEY, SLACK_WEBHOOK_URL
```

### 5.3 Supabase
- [ ] Bucket: `jobdigger-pdfs` (openbare lezing)

### 5.4 Lemlist campagne
| Touch | Dag | Inhoud |
|-------|-----|--------|
| 1 | 0 | Vacatureanalyse (PDF) |
| 2 | 3 | Doelgroepenrapport (PDF) |
| 3 | 6 | Salarispositionering |
| 4 | 10 | Landingspagina preview |
| 5 | 13 | Soft ask |

### 5.5 Lokale .env
```
ANTHROPIC_API_KEY=sk-ant-...
LEMLIST_API_KEY=1d1709e871...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJhbGc...
```

### 5.7 Test run (16 mei 14:00)
- [ ] `LEAD_BATCH_SIZE = 5`
- [ ] Handmatige trigger via workflow_dispatch
- [ ] Verifieer Lemlist + Supabase

### 5.8 Pre-live audit (17 mei 07:00)
- [ ] Alle 7 geheimen geconfigureerd
- [ ] Scraper output 200/dag
- [ ] ICP filter selecteert 20-30

### 5.9 Live (17 mei 08:00)
- [ ] `LEAD_BATCH_SIZE = 20`
- [ ] Laatste git push
- [ ] Monitor eerste 2 uur

## 📊 Succesmetrieken (Week 1)

| Metriek | Doel |
|---------|------|
| Leads/dag | 20 |
| ICP slagingspercentage | 15-20% |
| PDF render succes | >95% |
| Antwoordtarief T1-5 | 8-12% |

## 💰 Maandelijkse kosten

| Service | Kosten |
|---------|--------|
| Claude API | €27,60 |
| Lemlist | €60,00 |
| Supabase | €4,50 |
| **TOTAAL** | **€92,10** |

**Inkomstendoel M2:** €600-1.800 | **ROI:** 6-19x

## 🚨 Terugdraaiing
```bash
gh workflow disable daily-cron.yml
python test_full_pipeline.py
gh workflow enable daily-cron.yml
```