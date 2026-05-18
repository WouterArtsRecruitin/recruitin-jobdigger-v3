# 📋 GITHUB ONBOARDING — JobDigger V3 Fase 5

## STAP 1: Push repository
```bash
cd /home/claude/projects/jobdigger-email-automation/
git push -u origin main
```

Verifieer op: https://github.com/WouterArtsRecruitin/recruitin-jobdigger-v3

---

## STAP 2: Voeg geheimen toe

**Settings → Secrets and variables → Actions → New repository secret**

| Geheim | Waarde | Notitie |
|--------|--------|---------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Je Anthropic console |
| `LEMLIST_API_KEY` | `1d1709e871748ecaf06df5309992efc6` | Verified |
| `SUPABASE_URL` | `https://...supabase.co` | Je Supabase project |
| `SUPABASE_KEY` | `eyJhbGc...` | Service key (write) |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/...` | Optional |
| `SLACK_CHANNEL_ID` | `C024BE91L` | Optional |
| `LEAD_BATCH_SIZE` | `5` | Test; later: `20` |

---

## STAP 3: Schakel Actions in

**Settings → Actions → General**
- ✅ "Allow all actions and reusable workflows"

---

## STAP 4: Setup Services

### **Supabase:**
1. Maak bucket aan: `jobdigger-pdfs`
2. Rechten: Public Read + Auth Write
3. Get `SUPABASE_URL` en `SUPABASE_KEY`

### **Lemlist:**
1. Verifieer API-key: `1d1709e871748ecaf06df5309992efc6` ✓
2. Maak campagne aan:
   - Naam: "JobDigger P12 - Stage 2 Optimized"
   - 5 touches × 14 dagen
3. Setup sequence details

### **Slack (optioneel):**
1. Create incoming webhook
2. Get URL + Channel ID

---

## STAP 5: Test workflow

**Actions → JobDigger Daily Automation → Run workflow**

### **Expected output:**
```
[INFO] Scraping 200 vacancies from daily_vacancies.json
[INFO] ICP filter applied: 20 qualified leads
[INFO] ✓ Generated: test_001_touch1_vacature.pdf (42KB)
[INFO] ✓ Generated: test_001_touch2_doelgroep.pdf (34KB)
[INFO] ✓ Created Lemlist contact: test001@testcorp.nl
[INFO] Pipeline completed: 20 processed | 0 errors | 215.3s
```

---

## STAP 6: Verify results

**Supabase:** Check bucket `jobdigger-pdfs` → ~40 bestanden (2 per lead × 20)

**Lemlist:** 20 nieuwe contacten aangemaakt

---

## Probleemoplossing

| Probleem | Oplossing |
|----------|-----------|
| Workflow draait niet | Wacht 15 min of handmatige trigger |
| PDF render error | Check WeasyPrint + fonts |
| Lemlist 401 | Verify API key in Secrets |
| Supabase permission denied | Set bucket to public read |
| Claude timeout | Verhoog timeout=30 in script |

---

## Volgende stap

→ STAP 7: **Test run op 16 mei 14:00**