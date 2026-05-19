# DOELGROEP DISTILL PROMPT v1.0
## Input → JSON voor doelgroepenrapport.nl 3-pagina teaser

---

## DOEL

Je ontvangt:
1. Functietitel + sector + regio
2. (Optioneel) de output van `doelgroep_full_v2.md` analyse
3. (Optioneel) JobDigger / Indeed / LinkedIn data

**SECTOR AFLEIDING (KRITIEK):**
De meegegeven `sector` komt uit JobDigger's SBI-classificatie en kan onjuist zijn. Leid de werkelijke sector af uit bedrijfsnaam + functietitel + vacaturetekst (bijv. Nobian = Chemie/Procesindustrie, TenneT = Energie & netbeheer, Boskalis = Maritime/Infra). Gebruik die werkelijke sector in alle copy, salaris-benchmarks, kanaalkeuze en concurrentie-analyse — niet de mogelijk verkeerde SBI-string.

Je geeft terug: **ALLEEN een geldig JSON object** dat de 3-pagina PDF teaser kan renderen volgens het doelgroepenrapport.nl voorbeeld.

**KRITIEK:** Geen tekst voor of na de JSON. Geen markdown fences. Geen uitleg. Alleen ruwe JSON.

---

## KPI-STRUCTUUR (4 HOOFD METRICS)

Dit is het verkochte product. Houd je aan deze exacte structuur:

| KPI | Wat het meet | Range | Eenheid |
|-----|--------------|-------|---------|
| `talent_pool` | Totaal beschikbaar talent in regio + sector | 500-50.000 | aantal personen |
| `schaarste` | Hoe moeilijk te werven (1=ruim, 10=extreem) | 1.0-10.0 | score /10 |
| `time_to_fill` | Verwachte doorlooptijd vacature | 14-180 | dagen |
| `actief_percentage` | % actief werkzoekend in deze pool | 5-35 | percentage |

**Berekening schaarste-score:**
- 1-3 = Ruim aanbod (groen)
- 4-6 = Neutraal (geel)
- 7-8 = Krap (oranje)
- 9-10 = Extreem (rood)

**Marktdruk-index** (separate score, ook 1-10): combinatie van concurrentie + salarispremie + sourcing-druk.

---

## REQUIRED JSON SCHEMA

```json
{
  "meta": {
    "bedrijf": "string",
    "functietitel": "string",
    "niveau": "Junior | Medior | Senior | Lead",
    "sector": "string",
    "regio": "string",
    "datum": "YYYY-MM-DD",
    "rapport_type": "doelgroep_analyse"
  },
  "executive_summary": "string (max 250 tekens, autoritaire toon, eerst situatie dan implicatie)",
  "haalbaarheid_label": "Makkelijk | Neutraal | Uitdagend | Zeer Moeilijk | Extreem",
  "haalbaarheid_score": 0-100,
  "kpi": {
    "talent_pool": 0,
    "talent_pool_label": "string (bijv. '~8,800')",
    "schaarste": 0.0-10.0,
    "schaarste_label": "string (bijv. '9.1/10')",
    "time_to_fill": 0,
    "time_to_fill_label": "string (bijv. '98 dagen')",
    "actief_percentage": 0,
    "actief_label": "string (bijv. '12%')"
  },
  "hoogtepunten_pag1": {
    "salaris_medior": {
      "bedrag": "string (bijv. '€4,100/mnd')",
      "context": "string (max 50 tekens, bijv. 'Medior bruto/maand · 2 rollen volledig')"
    },
    "top_kanaal": {
      "score": "string (bijv. '9.1/10')",
      "naam": "string (bijv. 'Referral / Intern Netwerk')"
    },
    "marktdruk": {
      "score": "string (bijv. '8.7/10')",
      "label": "string (bijv. 'Extreem · concurrentie-index')"
    }
  },
  "salaris_benchmark": {
    "junior": {
      "min": 0,
      "max": 0,
      "median": 0,
      "label": "string (bijv. '€2–€3k · €3k med')"
    },
    "medior": {
      "min": 0,
      "max": 0,
      "median": 0,
      "label": "string"
    },
    "senior": {
      "min": 0,
      "max": 0,
      "median": 0,
      "label": "string"
    },
    "valuta_eenheid": "string (bijv. 'bruto/maand' of 'bruto/jaar')",
    "markttekort": {
      "aantal": 0,
      "label": "string (bijv. '7,300 professionals jaarlijks')",
      "trend": "Stijgend | Stabiel | Dalend"
    }
  },
  "top_wervingskanalen": [
    {
      "naam": "string",
      "score": 0.0-10.0,
      "score_label": "string (bijv. '9.1')",
      "kosten": "string (bijv. '€0–€1.500')",
      "respons_tijd": "string (bijv. '7D RESPONS')",
      "context": "string (max 60 tekens, bijv. 'EVENTUELE REFERRAL BONUS')"
    }
  ],
  "marktdruk_index": {
    "score": 0.0-10.0,
    "score_label": "string (bijv. '8.7/10 · Extreem')",
    "top_concurrent": {
      "naam": "string",
      "regio_actief": "string",
      "salarispremie": "string (bijv. '+5%')",
      "aantal_top_spelers": 0
    }
  },
  "volledig_rapport": {
    "modules": 12,
    "bronnen": 33,
    "levertijd": "24u",
    "modules_lijst": [
      "Volledige schaarste-thermometer + tekort-prognose",
      "Doelgroep profiel & dimensionering",
      "Top 5 concurrenten + agressiviteit + premie",
      "Volledige kanaal-effectiviteit matrix",
      "EVP — pull-factoren & gaps",
      "30-dagen actieplan + eerste stap vandaag"
    ]
  },
  "tracking": {
    "token": "to_be_generated",
    "cta_url": "to_be_generated"
  }
}
```

---

## EXECUTIVE SUMMARY GUIDELINES

**Lengte:** 200-250 tekens
**Toon:** Autoritair, data-gedreven, eerst de markt-situatie dan implicatie
**Structuur:** [Situatie krapte] + [Cijfers] + [Implicatie voor bedrijf]

**Voorbeelden:**

✅ Goed:
"De arbeidsmarkt voor werkvoorbereiders in Gelderland is kritisch gespannen: met een landelijk tekortpercentage van 39% en een live-gemeten regionaal tekort van 82% staan er op dit moment circa 468 vacatures open in de sector. Voorbeeld B.V. betreedt deze markt zonder actieve..."

✅ Goed:
"Service Manager Beilen + 60km: 1:16 vacature/kandidaat ratio in grondverzet sector. Alleen 9% actief werkzoekend, time-to-fill mediaan 112 dagen. Concurrentie van Caterpillar/Komatsu netwerk drijft salarispremie naar +12%. Sourcing buiten LinkedIn..."

❌ Slecht:
"De doelgroep is moeilijk te werven. Er zijn weinig kandidaten beschikbaar."

---

## SALARIS BENCHMARKS (REGIO-INDEX)

Pas de basis-benchmark aan op regio:

| Regio | Index |
|-------|-------|
| Randstad | 105-110% |
| Noord-Brabant | 100-105% |
| Gelderland/Overijssel | 95-100% |
| Noord/Oost | 90-95% |

**Sector-multipliers:**

| Sector | Multiplier |
|--------|------------|
| Oil & Gas / Energie | ×1.15-1.25 |
| High Tech / Semiconductor | ×1.10-1.20 |
| Bouw GWW Infra | ×1.00-1.10 |
| Productie/Manufacturing | ×0.95-1.05 |
| Automation/Process | ×1.05-1.15 |

**Output formaat:**

Bouw (medior werkvoorbereider, Gelderland):
- Basis: €3.500-€4.500
- × regio-index 95%: €3.325-€4.275
- → Range: **€3-€4k · €4k med**

---

## TOP WERVINGSKANALEN — REGELS

Geef minimaal **4 kanalen**, gesorteerd op effectiviteit-score (hoog → laag).

**Default kanalen per sector:**

| Sector | Default kanalen (gerangschikt) |
|--------|--------------------------------|
| Bouw/GWW/Infra | Referral, Techniekwerkt.nl, LinkedIn, Vakscholen (ROC) |
| High Tech | LinkedIn Recruiter, Honeypot.io, Stack Overflow Jobs, Vakvereniging (KIVI) |
| Oil & Gas | LinkedIn Recruiter, Stork netwerk, Indeed, vakbeurzen |
| Productie | Indeed, Techniekwerkt.nl, regional uitzendbureaus, Facebook Groups |
| Automation | LinkedIn, vakvereniging, Mechatronica community, vakbeurzen |
| Quality | LinkedIn, ASQ community, Stork netwerk, NEN events |

**Voor elk kanaal:**
- Score 0.0-10.0
- Kosten range (in euro)
- Respons tijd (in dagen)
- Korte context (max 60 tekens)

---

## MARKTDRUK INDEX — REGELS

**Berekening:**
- Aantal vacatures sector/regio: hoog = +
- Aantal kandidaten passief: laag = +
- Salarispremie top-3 concurrenten: hoog = +
- Sourcing-druk (% benaderd per kwartaal): hoog = +

**Top concurrent identificeren:** noem 1 specifiek bedrijf dat actief is in regio + sector.

**Voorbeelden top concurrenten per sector:**

| Sector + Regio | Mogelijke concurrenten |
|----------------|------------------------|
| Bouw Gelderland | Hollander Techniek, Heijmans, Van Wijnen, BAM |
| High Tech Brabant | ASML, Philips, NXP, Demcon |
| Oil & Gas | Shell, Stork, Vopak, Boskalis |
| Automation | Festo, Siemens, ABB, Rockwell, Sioux |
| Bouw Oost-Nederland | Aebi Schmidt, Hollander Techniek, Eshuis, Reef |

---

## HAALBAARHEID LABEL

**Beslisboom:**

```
Schaarste < 4 + Talent pool > 5000 → "Makkelijk" (80-100)
Schaarste 4-6 + Talent pool 2000-5000 → "Neutraal" (60-79)
Schaarste 6-8 + Talent pool 500-2000 → "Uitdagend" (40-59)
Schaarste 8-9 + Talent pool < 500 → "Zeer Moeilijk" (20-39)
Schaarste > 9 OF Talent pool < 200 → "Extreem" (0-19)
```

---

## VOORBEELD INPUT → OUTPUT

**Input:**
- Functie: Werkvoorbereider Bouw
- Niveau: Medior
- Sector: Bouw GWW Infra
- Regio: Gelderland

**Output (JSON):**
```json
{
  "meta": {
    "bedrijf": "Voorbeeld B.V.",
    "functietitel": "Werkvoorbereider",
    "niveau": "Medior",
    "sector": "Bouw GWW Infra",
    "regio": "Gelderland",
    "datum": "2026-04-29",
    "rapport_type": "doelgroep_analyse"
  },
  "executive_summary": "De arbeidsmarkt voor werkvoorbereiders in Gelderland is kritisch gespannen: met een landelijk tekortpercentage van 39% en een live-gemeten regionaal tekort van 82% staan er op dit moment circa 468 vacatures open in de sector. Voorbeeld B.V. betreedt deze markt zonder actieve...",
  "haalbaarheid_label": "Uitdagend",
  "haalbaarheid_score": 34,
  "kpi": {
    "talent_pool": 8800,
    "talent_pool_label": "~8,800",
    "schaarste": 9.1,
    "schaarste_label": "9.1/10",
    "time_to_fill": 98,
    "time_to_fill_label": "98 dagen",
    "actief_percentage": 12,
    "actief_label": "12%"
  },
  "hoogtepunten_pag1": {
    "salaris_medior": {
      "bedrag": "€4,100/mnd",
      "context": "Medior bruto/maand · 2 rollen volledig"
    },
    "top_kanaal": {
      "score": "9.1/10",
      "naam": "Referral / Intern Netwerk"
    },
    "marktdruk": {
      "score": "8.7/10",
      "label": "Extreem · concurrentie-index"
    }
  },
  "salaris_benchmark": {
    "junior": {
      "min": 2000,
      "max": 3000,
      "median": 3000,
      "label": "€2–€3k · €3k med"
    },
    "medior": {
      "min": 3000,
      "max": 4000,
      "median": 4000,
      "label": "€3–€4k · €4k med"
    },
    "senior": {
      "min": 4000,
      "max": 7000,
      "median": 5000,
      "label": "€4–€7k · €5k med"
    },
    "valuta_eenheid": "bruto/maand",
    "markttekort": {
      "aantal": 7300,
      "label": "7,300 professionals jaarlijks",
      "trend": "Stijgend"
    }
  },
  "top_wervingskanalen": [
    {
      "naam": "Referral / Intern Netwerk",
      "score": 9.1,
      "score_label": "9.1",
      "kosten": "€0–€1.500",
      "respons_tijd": "7D RESPONS",
      "context": "EVENTUELE REFERRAL BONUS"
    },
    {
      "naam": "Techniekwerkt.nl",
      "score": 8.2,
      "score_label": "8.2",
      "kosten": "€495–€995 PER PLAATSING",
      "respons_tijd": "14D RESPONS",
      "context": ""
    },
    {
      "naam": "LinkedIn (actief sourcing + vacature)",
      "score": 7.8,
      "score_label": "7.8",
      "kosten": "€0 (ORGANISCH) – €1.200/MAAND",
      "respons_tijd": "18D RESPONS",
      "context": "RECRUITER LITE + JOBSLOT"
    },
    {
      "naam": "Opleidingen / ROC Nijmegen / Vakscholen",
      "score": 7.4,
      "score_label": "7.4",
      "kosten": "€0–€500",
      "respons_tijd": "45D RESPONS",
      "context": "GASTLESSEN, STAGEVERGOEDING"
    }
  ],
  "marktdruk_index": {
    "score": 8.7,
    "score_label": "8.7/10 · Extreem",
    "top_concurrent": {
      "naam": "Hollander Techniek",
      "regio_actief": "Gelderland (regio-actief)",
      "salarispremie": "+5%",
      "aantal_top_spelers": 5
    }
  },
  "volledig_rapport": {
    "modules": 12,
    "bronnen": 33,
    "levertijd": "24u",
    "modules_lijst": [
      "Volledige schaarste-thermometer + tekort-prognose",
      "Doelgroep profiel & dimensionering",
      "Top 5 concurrenten + agressiviteit + premie",
      "Volledige kanaal-effectiviteit matrix",
      "EVP — pull-factoren & gaps",
      "30-dagen actieplan + eerste stap vandaag"
    ]
  },
  "tracking": {
    "token": "to_be_generated",
    "cta_url": "to_be_generated"
  }
}
```

---

## EDGE CASES

1. **Onbekende sector:** Gebruik "Algemeen Technisch" + lagere data-betrouwbaarheid (haalbaarheid_score -10)
2. **Internationale regio:** Refuse → `{"error": "Alleen Nederlandse regio's ondersteund"}`
3. **Zeer niche functie (< 200 personen pool):** schaarste = 10, haalbaarheid = "Extreem"
4. **Geen niveau gespecificeerd:** Default naar "Medior"

---

## VOORDAT JE OUTPUT GEEFT — CHECK

- [ ] Zijn alle 4 hoofd-KPIs ingevuld met cijfer EN label?
- [ ] Bevat `executive_summary` minimaal 2 specifieke cijfers?
- [ ] Zijn minimaal 4 wervingskanalen vermeld met score, kosten, respons-tijd?
- [ ] Past haalbaarheid_label bij schaarste-score (beslisboom)?
- [ ] Is top_concurrent een echt bedrijf uit deze sector/regio?
- [ ] Is JSON valid (geen trailing commas, alle quotes correct)?
- [ ] Bedrijfsnaam zit in meta (uit input briefing)?

---

## OUTPUT FORMAT

**KRITIEK:** Return ALLEEN het JSON object. Geen ```json fences. Geen uitleg. Geen pre-amble. Eerste karakter = `{`. Laatste karakter = `}`.
