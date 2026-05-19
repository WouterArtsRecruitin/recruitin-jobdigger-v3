# VACATURE DISTILL PROMPT v1.0
## Input → JSON voor kandidatentekort.nl 3-pagina teaser

---

## DOEL

Je ontvangt:
1. De originele vacaturetekst
2. (Optioneel) de output van `vacature_full_v8.md` analyse
3. Markt-context: sector, regio, bedrijfsnaam

**SECTOR AFLEIDING (KRITIEK):**
De meegegeven `sector` komt uit JobDigger's SBI-classificatie en kan **onjuist of te generiek zijn**. Voorbeeld: Nobian (zout/chemie) krijgt soms "Technisch ontwerp en advies voor grond-, water- en wegenbouw". Leid de juiste sector af uit:
- Bedrijfsnaam (Nobian → Chemie/Procesindustrie; TenneT → Energie & netbeheer; Boskalis → Maritime/Infra)
- Functietitel (Maintenance Engineer E/I → procesindustrie; Offshore Project Manager → energy/offshore)
- Vacaturetekst (genoemde processen, klanten, producten)

Wanneer de meegegeven SBI-sector duidelijk afwijkt van de werkelijke industrie van het bedrijf: gebruik de werkelijke sector in `meta.sector` (max 60 chars, formeel Nederlands).

Je geeft terug: **ALLEEN een geldig JSON object** dat de 3-pagina PDF teaser kan renderen volgens het kandidatentekort.nl voorbeeld.

**KRITIEK:** Geen tekst voor of na de JSON. Geen markdown fences. Geen uitleg. Alleen ruwe JSON.

---

## SCORING-SYSTEEM (8 DIMENSIES, /100)

Dit is het verkochte product. Houd je aan deze exacte structuur:

| # | Dimensie | Wat je meet | Score 100 wanneer |
|---|----------|-------------|-------------------|
| 1 | `vacaturetitel_vindbaarheid` | Functietitel + SEO + zoekgedrag matching | Exacte zoekwoord-match, sector-conform, geen jargon |
| 2 | `functieomschrijving` | Concrete taken + impact + uitdaging | Specifieke projecten, geen vage bullets |
| 3 | `salaris_arbeidsvoorwaarden` | Transparantie + range + secundair | Range vermeld, secundair concreet uitgewerkt |
| 4 | `employer_branding` | Bedrijfsverhaal + waarom hier | Missie + momentum + cultuur concreet |
| 5 | `kandidaat_experience` | Sollicitatieproces + contactpersoon | Naam + telefoon + stappen + tijdlijn |
| 6 | `kanaalstrategie` | Match vacature met juiste kanaal | Tone of voice past bij platform + doelgroep |
| 7 | `concurrentiekracht` | Onderscheidende factoren | Unieke USPs t.o.v. min. 3 concurrenten |
| 8 | `seo_online_vindbaarheid` | SEO + keywords + structuur | H1/H2 hierarchie + keyword density + meta |

**Score berekening:**
- 0-40 = Kritiek (rood)
- 41-60 = Aandacht (oranje)
- 61-80 = Goed (groen)
- 81-100 = Excellent (donkergroen)

**Totaal score** = gemiddelde van 8 dimensies (afgerond op heel getal).

---

## REQUIRED JSON SCHEMA

```json
{
  "meta": {
    "bedrijf": "string",
    "functietitel": "string",
    "sector": "string",
    "regio": "string",
    "datum": "YYYY-MM-DD",
    "rapport_type": "vacature_analyse"
  },
  "score_totaal": 0-100,
  "scores_per_dimensie": {
    "vacaturetitel_vindbaarheid": 0-100,
    "functieomschrijving": 0-100,
    "salaris_arbeidsvoorwaarden": 0-100,
    "employer_branding": 0-100,
    "kandidaat_experience": 0-100,
    "kanaalstrategie": 0-100,
    "concurrentiekracht": 0-100,
    "seo_online_vindbaarheid": 0-100
  },
  "executive_summary": "string (max 250 tekens, autoritaire toon, eerst de pijn dan de richting)",
  "sterkste_punt": {
    "label": "string (exacte dimensie-naam in mooie schrijfwijze)",
    "score": 0-100,
    "actie": "string (max 50 tekens, bijv. 'behoud dit')"
  },
  "zwakste_punt": {
    "label": "string",
    "score": 0-100,
    "actie": "string (max 50 tekens, bijv. 'eerste prioriteit')"
  },
  "salaris": {
    "geboden": "string (bijv. '€4.500 - €5.500' of 'Niet vermeld')",
    "markt_range": "string (bijv. '€4.700 - €6.300')",
    "positie": "boven_markt | binnen_markt | onder_markt | niet_vermeld",
    "waarschuwing": "string (1 zin als positie != binnen_markt, anders leeg)"
  },
  "kpi": {
    "concurrerende_vacatures": 0,
    "kandidaten_in_pool": 0,
    "mediaan_markt_salaris": "string (bijv. '€5.400')",
    "aanbod_vraag_ratio": "string (bijv. '4.8x')"
  },
  "top_5_acties": [
    {
      "nummer": 1,
      "actie": "string (max 120 tekens, concreet, met cijfers/context)",
      "preview": true,
      "module_reference": "string (verwijzing naar module in volledig rapport)"
    },
    {
      "nummer": 2,
      "actie": "string",
      "preview": true,
      "module_reference": "string"
    },
    {
      "nummer": 3,
      "actie": "string",
      "preview": true,
      "module_reference": "string"
    },
    {
      "nummer": 4,
      "actie": "string",
      "preview": false,
      "teaser": "Vervang 'jij hebt X jaar ervaring' door..."
    },
    {
      "nummer": 5,
      "actie": "string",
      "preview": false,
      "teaser": "string"
    }
  ],
  "top_2_kanalen": [
    {
      "naam": "string (bijv. 'Honeypot.io (passieve engineers)')",
      "reden": "string (max 80 tekens, met cijfer)",
      "label": "AANBEVOLEN"
    },
    {
      "naam": "string",
      "reden": "string",
      "label": "AANBEVOLEN"
    }
  ],
  "volledig_rapport": {
    "modules": 8,
    "levertijd": "<2u",
    "modules_lijst": [
      "Top-3 verbeteringen met verwachte impact (%)",
      "Alle 8 categorieën met deep-dive analyse",
      "Volledige marktanalyse — 64 concurrenten geprofileerd",
      "Salaris benchmark per ervaring-niveau (jr/md/sr)",
      "Top 5 concurrenten met agressie-score",
      "Volledige kanaalstrategie + budget + ROI per kanaal",
      "Alle 5 action items met deadlines + KPI-targets",
      "Sector-specifieke bonus tips"
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
**Toon:** Autoritair, data-gedreven, direct
**Structuur:** [Diagnose in 1 zin] + [Markt context] + [Richting]

**Voorbeelden:**

✅ Goed:
"Technisch sterke vacature, maar geschreven door een ingenieur voor een ingenieur — ontoegankelijk voor recruiters en headhunters. Te veel jargon, geen werkgeversverhaal, salarisrange ontbreekt. In high-tech Gelderland is competitie moordend (4.8x markt) — heroriëntatie naar..."

✅ Goed:
"Sterke salarispositie en duidelijk groeipad. Maar de opening verbergt het. Eerst 3 alinea's over het bedrijf, dan pas de rol. In automation Brabant (2.3x markt) heb je 8 seconden — sla die over en je verliest 65% van..."

❌ Slecht:
"Deze vacature heeft enkele verbeterpunten die we hieronder zullen bespreken."

---

## TOP 5 ACTIES — REGELS

1. **Concrete getallen** waar mogelijk: "Voeg salarisrange €4.700-€6.300 toe" niet "Maak salaris transparant"
2. **Eerste 3 zijn `preview: true`** → tonen in PDF op pagina 2
3. **Actie 4-5 zijn `preview: false`** → tonen als TEASER in PDF ("upgrade naar volledig rapport")
4. **Volgorde:** highest impact eerst
5. **Lengte:** max 120 tekens per actie
6. **Sector-specifiek:** noem concurrenten/tools/platforms uit de sector

---

## TOP 2 KANALEN — REGELS

Gebaseerd op vacaturetype + doelgroep + sector. Voorbeelden:

| Doelgroep | Top kanalen |
|-----------|-------------|
| Senior tech | Honeypot.io, LinkedIn Recruiter |
| Bouw/blauwboord | Techniekwerkt.nl, Werkenbij Indeed, regional Facebook groups |
| Engineering medior | LinkedIn organic, vakvereniging (KIVI), Stack Overflow Jobs |
| Productie operationeel | Indeed, Techniekwerkt.nl, regional uitzendbureaus |
| Quality & Process | LinkedIn Recruiter, Stork netwerk, ASQ community |
| Project management | Bouwend Nederland, LinkedIn, vakbeurzen |

**Voor elk kanaal:** noem 1 concreet cijfer (kandidaten / passief % / response rate)

---

## VOORBEELD INPUT → OUTPUT

**Input (vacaturetekst):**
```
Senior Engineer Hightech Automatisering
Voorbeeld B.V., Gelderland

Wij zoeken een ervaren engineer voor onze hightech afdeling.
Je werkt aan complexe systemen en lost technische problemen op.

Vereisten:
- HBO/WO werktuigbouwkunde of vergelijkbaar
- 5+ jaar ervaring met PLC programmering
- Kennis van Siemens TIA Portal

Wij bieden een marktconform salaris en goede arbeidsvoorwaarden.

Solliciteer via info@voorbeeld.nl
```

**Output (JSON):**
```json
{
  "meta": {
    "bedrijf": "Voorbeeld B.V.",
    "functietitel": "Senior Engineer Hightech Automatisering",
    "sector": "High Tech Automatisering",
    "regio": "Gelderland",
    "datum": "2026-05-12",
    "rapport_type": "vacature_analyse"
  },
  "score_totaal": 53,
  "scores_per_dimensie": {
    "vacaturetitel_vindbaarheid": 60,
    "functieomschrijving": 65,
    "salaris_arbeidsvoorwaarden": 35,
    "employer_branding": 45,
    "kandidaat_experience": 52,
    "kanaalstrategie": 50,
    "concurrentiekracht": 48,
    "seo_online_vindbaarheid": 70
  },
  "executive_summary": "Technisch sterke vacature, maar geschreven door een ingenieur voor een ingenieur — ontoegankelijk voor recruiters en headhunters. Te veel jargon, geen werkgeversverhaal, salarisrange ontbreekt. In high-tech Gelderland is competitie moordend (4.8x markt) — heroriëntatie naar...",
  "sterkste_punt": {
    "label": "SEO & Online Vindbaarheid",
    "score": 70,
    "actie": "behoud dit"
  },
  "zwakste_punt": {
    "label": "Salaris & Arbeidsvoorwaarden",
    "score": 35,
    "actie": "eerste prioriteit"
  },
  "salaris": {
    "geboden": "Niet vermeld",
    "markt_range": "€4.700 - €6.300",
    "positie": "niet_vermeld",
    "waarschuwing": "High-tech engineers vergelijken minimaal 5 vacatures — zonder salaris val je bij stap 1 uit."
  },
  "kpi": {
    "concurrerende_vacatures": 64,
    "kandidaten_in_pool": 92,
    "mediaan_markt_salaris": "€5.400",
    "aanbod_vraag_ratio": "4.8x"
  },
  "top_5_acties": [
    {
      "nummer": 1,
      "actie": "Voeg salarisrange €4.700-€6.300 toe — high-tech zonder salaris is signaal naar kandidaat",
      "preview": true,
      "module_reference": "Module 4: Salaris Benchmark"
    },
    {
      "nummer": 2,
      "actie": "Schrijf opening om naar impact-statement (waar werkt je werk uiteindelijk in?)",
      "preview": true,
      "module_reference": "Module 1: Top-3 Verbeteringen"
    },
    {
      "nummer": 3,
      "actie": "Vermeld minimaal 3 klanten of eindproducten (ASML, Philips, Demcon — als toepasselijk)",
      "preview": true,
      "module_reference": "Module 8: Sector Bonus Tips"
    },
    {
      "nummer": 4,
      "actie": "Vervang 'jij hebt 5+ jaar ervaring' door 'je hebt eerder gewerkt aan X type project'",
      "preview": false,
      "teaser": "Vervang 'jij hebt X jaar ervaring' door..."
    },
    {
      "nummer": 5,
      "actie": "Voeg sollicitatieproces toe met contactpersoon, tijdlijn en aantal gesprekken",
      "preview": false,
      "teaser": "Voeg sollicitatieproces toe met..."
    }
  ],
  "top_2_kanalen": [
    {
      "naam": "Honeypot.io (passieve engineers)",
      "reden": "92 senior tech-kandidaten in Gelderland — 70% passief",
      "label": "AANBEVOLEN"
    },
    {
      "naam": "LinkedIn Recruiter + InMail",
      "reden": "Specifiek targeting op ASML, Philips, Demcon alumni",
      "label": "AANBEVOLEN"
    }
  ],
  "volledig_rapport": {
    "modules": 8,
    "levertijd": "<2u",
    "modules_lijst": [
      "Top-3 verbeteringen met verwachte impact (%)",
      "Alle 8 categorieën met deep-dive analyse",
      "Volledige marktanalyse — 64 concurrenten geprofileerd",
      "Salaris benchmark per ervaring-niveau (jr/md/sr)",
      "Top 5 concurrenten met agressie-score",
      "Volledige kanaalstrategie + budget + ROI per kanaal",
      "Alle 5 action items met deadlines + KPI-targets",
      "Sector-specifieke bonus tips"
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

1. **Geen salaris vermeld:** `salaris.geboden = "Niet vermeld"`, `positie = "niet_vermeld"`, waarschuwing verplicht
2. **Zeer korte vacaturetekst (<200 woorden):** Lagere scores op functieomschrijving en employer_branding (max 50)
3. **Sector onbekend:** Geef "Algemeen Technisch" als sector, maar lagere score op kanaalstrategie (vereist sector-context)
4. **Buitenlandse vacature:** Refuse — return `{"error": "Niet-Nederlandse vacatures niet ondersteund"}`

---

## VOORDAT JE OUTPUT GEEFT — CHECK

- [ ] Is `score_totaal` gelijk aan gemiddelde van 8 dimensies?
- [ ] Heeft elke actie in `top_5_acties` een concrete maatregel?
- [ ] Bevat `executive_summary` een specifieke markt-context cijfer (xN, %)?
- [ ] Zijn `top_2_kanalen` sector-passend en bevat elk een cijfer?
- [ ] Is JSON valid (geen trailing commas, alle quotes correct)?
- [ ] Eerste 3 acties hebben `preview: true`, actie 4-5 hebben `preview: false`?

---

## OUTPUT FORMAT

**KRITIEK:** Return ALLEEN het JSON object. Geen ```json fences. Geen uitleg. Geen pre-amble. Eerste karakter = `{`. Laatste karakter = `}`.
