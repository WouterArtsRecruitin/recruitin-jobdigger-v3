# Lemlist V3 P12 Campaign Setup Guide

**Campaign ID:** `cam_B3BDF7MeBCcTN3CtS`  
**Campaign URL:** https://app.lemlist.com/campaigns/cam_B3BDF7MeBCcTN3CtS/sequence

---

## Step 1: Open Campaign

1. Go to https://app.lemlist.com/campaigns/cam_B3BDF7MeBCcTN3CtS/sequence
2. You should see an empty sequence

---

## Step 2: Add Touch 1 (Day 0) — Vacature PDF

1. Click **"+ Add step"** or **"Add touch"**
2. **Type:** Email
3. **Subject:** `Vacature-analyse voor {{companyName}}`
4. **Body:**
   ```
   Hoi {{firstName|Beste}},

   Bijgevoegd je analyse van de {{jobTitle}}-vacature bij {{companyName}}.

   Gaat je dit rapport bekijken? (link naar PDF wordt per lead gegenereerd)

   —  
   Recruitin
   ```
5. **Delay:** Dag 0 (immediately)
6. **Attachment:** Will be auto-added by pipeline (don't set manually)
7. **Save**

---

## Step 3: Add Touch 2 (Day 2) — Doelgroep PDF

1. Click **"+ Add step"**
2. **Type:** Email
3. **Subject:** `Wie solliciteert op {{jobTitle}} in {{city}}?`
4. **Body:**
   ```
   Hoi {{firstName|Beste}},

   Bijgevoegd je doelgroeprapport voor {{jobTitle}} in {{city}}.

   Dit rapport toont wie de ideale kandidaat is en waar je ze vindt.

   Interessant? Lees de full analysis.

   —  
   Recruitin
   ```
5. **Delay:** Day 2 (2 days)
6. **Attachment:** Auto-added by pipeline
7. **Save**

---

## Step 4: Add Touch 3 (Day 5) — Soft Follow-up

1. Click **"+ Add step"**
2. **Type:** Email
3. **Subject:** `Korte vraag over je {{jobTitle}}-rapport`
4. **Body:**

Copy from `lemlist/touch3_followup.md`:

```
Hoi {{firstName|Beste}},

Ik heb je beide PDF's gestuurd:
- Vacature-analyse
- Doelgroeprapport

Veel zouden zeggen dat deze vacature een sterkte heeft in {{sterkste_dimensie}}. Klopt dat met je indruk?

Kort ja/nee/nog-niet?

—  
Recruitin
```

5. **Delay:** Day 5 (5 days from Touch 1)
6. **Save**

---

## Step 5: Add Touch 4 (Day 9) — Value-Add Insight

1. Click **"+ Add step"**
2. **Type:** Email
3. **Subject:** `1 cijfer over {{city}} dat opviel`
4. **Body:**

Copy from `lemlist/touch4_insight.md`:

```
Hoi {{firstName|Beste}},

In {{city}} zijn momenteel {{vacancies_count}} soortgelijke {{jobTitle}}-rollen openstaand.

Slechts {{qualified_candidates}}% van de sollicitanten haalt de screening.

Dat is je kans.

Wil je meer details?

—  
Recruitin
```

5. **Delay:** Day 9 (4 days after Touch 3)
6. **Save**

---

## Step 6: Add Touch 5 (Day 14) — Break-up

1. Click **"+ Add step"**
2. **Type:** Email
3. **Subject:** `Sluit ik het dossier {{companyName}}?`
4. **Body:**

Copy from `lemlist/touch5_breakup.md`:

```
Hoi {{firstName|Beste}},

Als ik niets van je hoor, sluit ik het dossier {{companyName}} over 3 maanden.

Daar ben je mee eens? Of wil je dat ik het open hou?

Kort antwoord volstaat 🙂

—  
Recruitin
```

5. **Delay:** Day 14 (5 days after Touch 4)
6. **Save**

---

## Step 7: Configure Campaign Settings

1. **Schedule:**
   - Time windows: **10:00 CET** + **14:00 CET**
   - Days: **Monday–Friday**

2. **Reply Detection:**
   - **Enable:** Yes (AAN)
   - This auto-moves replies to Pipedrive stage: "Lead Warm"

3. **Unsubscribe:**
   - **Enable:** Yes (AAN) — GDPR compliant

4. **Sender:**
   - **From:** `warts@recruitin.nl`
   - **Display name:** `Wouter Arts / Recruitin`

5. **Save campaign**

---

## Step 8: Verify

1. You should see 5 steps in the sequence
2. Delays should be: 0 → 2 → 5 → 9 → 14 days
3. All steps are marked as **Draft** until you're ready to activate

---

## Notes

- **Touch 1 & 2 PDFs:** These are generated per-lead by the pipeline. Lemlist will auto-attach them when the pipeline calls the API.
- **Variables:** `{{firstName|Beste}}`, `{{companyName}}`, `{{jobTitle}}`, `{{city}}` are all Lemlist variables. They auto-populate from the lead data.
- **Reply detection:** Replies trigger a webhook that updates Pipedrive (stage: "Lead Warm").
- **Unsubscribe:** Click removes the lead from the campaign (GDPR).

---

## Ready?

Once touches are set up, the pipeline can start sending leads automatically.
