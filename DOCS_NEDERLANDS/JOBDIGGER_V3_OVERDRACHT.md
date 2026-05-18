# JOBDIGGER V3 OVERDRACHT

## Overzicht

Geautomatiseerde recruitment funnel die dagelijks:
- 200 vacatures scrapt
- 20 gekwalificeerde leads filtert (6-gate ICP)
- 2 PDF's per lead genereert (Vacature + Doelgroep)
- Naar Lemlist uploadt (5-touch drip, 14 dagen)
- Hete leads detecteert via GA4/Meta Pixel

## Deliverables per fase

**FASE 1: Distillatie prompts** ✅
- `vacature_distill.md` (V8) — 8-dimensie score
- `doelgroep_distill.md` (V2) — 4 KPI's + salaris

**FASE 2: PDF-templates** ✅
- `touch1_vacature.html` → 42KB PDF
- `touch2_doelgroep.html` → 34KB PDF

**FASE 3: Web-templates** ✅
- `vacatura_web.html` → kandidatentekort.nl
- `doelgroep_web.html` → doelgroepenrapport.nl
- GA4 + Meta Pixel + hete lead detectie

**FASE 4: Automatisering** ✅
- `daily_automation.py` (440 regels, 6 classes)
- `daily-cron.yml` (GitHub Actions)
- `test_full_pipeline.py`

## Pipeline flow

```
data/daily_vacancies.json (scraper, 06:00 UTC)
  ↓ ICP filter (6 gates) → 20 gekwalificeerd
  ↓ Voer distills uit (Claude Opus)
  ↓ Render 2 PDF's/lead (WeasyPrint)
  ↓ Opslaan (Supabase + lokaal)
  ↓ Maak Lemlist contacten aan
  ↓ Klaar in 3-4 min (€3,07)
```

## Sleutelparameters

| Parameter | Waarde |
|-----------|--------|
| Dagelijkse leads | 20 |
| ICP slagingspercentage | 15-20% |
| Claude-model | claude-opus-4-20250514 |
| Max tokens | 8.000 |
| PDF-tool | WeasyPrint |
| GA4 ID | G-67PJ02SXVN |
| Meta Pixel | 238226887541404 |
| Cron | 07:00 UTC dagelijks |

## Mappenstructuur

```
/home/claude/projects/jobdigger-email-automation/
├── .github/workflows/daily-cron.yml
├── prompts/ (4 .md)
├── templates/ (4 .html)
├── scripts/daily_automation.py
├── test/
├── data/daily_vacancies.json
├── storage/pdfs/ (backup)
├── requirements.txt
└── .env (NIET gecommit)
```

## Ondertekening

✅ Fase 1-4 VOLTOOID — Klaar voor Fase 5 (17 mei deployment)