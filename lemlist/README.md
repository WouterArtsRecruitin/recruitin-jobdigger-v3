# Lemlist V3 P12 Campagne Copy

5-touch drip campagne over 14 dagen voor JobDigger V3 leads.

| Touch | Dag | Type | Bron |
|---|---|---|---|
| 1 | 0 | Vacature-analyse PDF | `templates/touch1_vacature.html` (gerenderd door pipeline) |
| 2 | 2 | Doelgroep-rapport PDF | `templates/touch2_doelgroep.html` (gerenderd door pipeline) |
| 3 | 5-6 | Soft follow-up | `lemlist/touch3_followup.md` |
| 4 | 9-10 | Value-add insight | `lemlist/touch4_insight.md` |
| 5 | 14 | Break-up | `lemlist/touch5_breakup.md` |

**Lemlist variables in copy:**
- `{{firstName|Beste}}` — fallback "Beste" als naam onbekend (NAAM_REGEL)
- `{{companyName}}`
- `{{jobTitle}}` (de geanalyseerde vacature)
- `{{city}}` (locatie bedrijf)

**From:** warts@recruitin.nl
**Reply detection:** AAN (push naar Pipedrive Stage "Lead Warm")
**Unsubscribe:** AAN (AVG verplicht)
**Verstuur-vensters:** 10:00 en 14:00 CET
