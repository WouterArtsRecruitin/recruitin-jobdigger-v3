# GITHUB ONBOARDING

## STAP 1: Push repository
```bash
cd /home/claude/projects/jobdigger-email-automation/
git push -u origin main
```

## STAP 2: Voeg geheimen toe (Settings → Secrets → Actions)

| Geheim | Waarde |
|--------|--------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `LEMLIST_API_KEY` | `1d1709e871748ecaf06df5309992efc6` |
| `SUPABASE_URL` | `https://...supabase.co` |
| `SUPABASE_KEY` | `eyJhbGc...` |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/...` |

## STAP 3: Schakel Actions in
**Settings → Actions → General** → ✅ Alle acties toestaan

## STAP 4: Setup Services

**Supabase:**
1. Maak bucket aan: `jobdigger-pdfs`
2. Rechten: Openbare lezing + Auth schrijven
3. Get URL + service key

**Lemlist:**
1. Verifieer API-sleutel ✓
2. Maak campagne aan: "JobDigger P12 - Stage 2 Optimized"
3. Setup 5 e-mailreeksen

## STAP 5: Test workflow
**Actions → JobDigger Daily Automation → "Workflow uitvoeren"**

Verwacht:
```
[INFO] 200 vacatures geladen
[INFO] ICP gekwalificeerd: 20/200
[INFO] ✓ Opgeslagen test_001_touch1_vacature.pdf (42KB)
[INFO] ✓ Lemlist contact aangemaakt: test@testcorp.nl
[INFO] Verwerkt: 20 | Succes: 20 | Tijd: 215.3s
```

## Mappenstructuur (GitHub)

```
recruitin-jobdigger-v3/
├── .github/workflows/daily-cron.yml
├── prompts/ (4 .md bestanden)
├── templates/ (4 .html bestanden)
├── scripts/daily_automation.py
├── test/, requirements.txt
├── test_full_pipeline.py
└── DEPLOYMENT_CHECKLIST.md
```

## Probleemoplossing

| Probleem | Oplossing |
|----------|-----------|
| Workflow draait niet om 07:00 UTC | Wacht 15 min of handmatige trigger |
| PDF render mislukt | Controleer WeasyPrint fonts |
| Lemlist 401 | Verifieer API-sleutel in Secrets |
| Supabase toestemming | Openbaar lezen + service key schrijven |
| Claude API timeout | Verhoog `timeout=30` |