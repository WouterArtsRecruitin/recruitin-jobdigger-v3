"""JobDigger V3 daily orchestrator.

Pipeline: load scraper output -> ICP filter -> Claude distills ->
WeasyPrint PDFs -> Supabase upload -> Lemlist contacts.

Invoked daily by .github/workflows/daily-cron.yml or manually:
    python scripts/daily_automation.py
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import anthropic
import pandas as pd
import requests
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from supabase import Client, create_client
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
TEMPLATES_DIR = ROOT / "templates"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    claude_model: str
    lemlist_api_key: str
    lemlist_campaign_id: str
    supabase_url: str
    supabase_key: str
    supabase_bucket: str
    slack_webhook_url: str | None
    lead_batch_size: int
    vacancies_path: Path
    pdf_dir: Path
    log_dir: Path
    min_icp_score: int = 90
    canary_email: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()

        def required(name: str) -> str:
            value = os.environ.get(name)
            if not value:
                raise RuntimeError(f"Missing required env var: {name}")
            return value

        # Auto-detect input file: prefer .xlsx if present, fallback to .json
        input_path = os.environ.get("VACANCIES_INPUT_PATH")
        if not input_path:
            xlsx = ROOT / "data" / "daily_vacancies.xlsx"
            input_path = "data/daily_vacancies.xlsx" if xlsx.exists() else "data/daily_vacancies.json"

        return cls(
            anthropic_api_key=required("ANTHROPIC_API_KEY"),
            claude_model=os.environ.get("CLAUDE_MODEL", "claude-opus-4-7"),
            lemlist_api_key=required("LEMLIST_API_KEY"),
            lemlist_campaign_id=required("LEMLIST_CAMPAIGN_ID"),
            supabase_url=required("SUPABASE_URL"),
            supabase_key=required("SUPABASE_KEY"),
            supabase_bucket=os.environ.get("SUPABASE_BUCKET", "jobdigger-pdfs"),
            slack_webhook_url=os.environ.get("SLACK_WEBHOOK_URL") or None,
            lead_batch_size=int(os.environ.get("LEAD_BATCH_SIZE", "20")),
            vacancies_path=ROOT / input_path,
            pdf_dir=ROOT / os.environ.get("PDF_OUTPUT_DIR", "storage/pdfs"),
            log_dir=ROOT / os.environ.get("LOG_DIR", "logs"),
            min_icp_score=int(os.environ.get("MIN_ICP_SCORE", "90")),
            canary_email=os.environ.get("CANARY_EMAIL") or None,
        )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"daily_run_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.log"

    logger = logging.getLogger("jobdigger")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(log_file)):
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger


# ---------------------------------------------------------------------------
# Stage 1: load vacancies
# ---------------------------------------------------------------------------


class VacancyLoader:
    """Load vacancies from JobDigger Excel (.xlsx) or JSON fixture.

    Accepts BOTH formats:
    - Raw JobDigger email-attachment (headers like "Functietitel", "Bedrijfsnaam",
      "Contactpersoon: E-mail", possibly with leading blank rows).
    - Processed JobDigger_Processed_*.xlsx (already normalized + ICP scored).

    Both are normalized to canonical V3 names (`title`, `company`, `contact_email`, …).
    """

    # Canonical Excel → V3 pipeline field map
    JOBDIGGER_COLUMN_MAP = {
        "Vacature": "title",
        "Bedrijf": "company",
        "Locatie": "location",
        "Regio": "region",
        "SBI_Sector": "sector",
        "Contact_Voornaam": "contact_first_name",
        "Contact_Achternaam": "contact_last_name",
        "Email": "contact_email",
        "Telefoon": "phone",
        "Website": "company_domain",
        "salarisindicatie": "salary",
        "URL": "vacancy_url",
        "KVK": "kvk",
        "SBI_Code": "sbi_code",
        "Score": "icp_score",
        "Prioriteit": "icp_priority",
        "Functie_Type": "functie_type",
        "beroep": "beroep",
        "opleiding": "opleiding",
    }

    # Raw JobDigger header aliases → canonical Excel name (lowercase keys for case-insensitive match)
    # Mirrors jobdigger_template_processor.normalize_columns
    RAW_ALIASES = {
        "bedrijfsnaam": "Bedrijf",
        "bedrijf": "Bedrijf",
        "organisatie": "Bedrijf",
        "company": "Bedrijf",
        "functietitel": "Vacature",
        "vacancy": "Vacature",
        "functie": "Vacature",
        "job_title": "Vacature",
        "vacature": "Vacature",
        "standplaats": "Locatie",
        "plaats": "Locatie",
        "city": "Locatie",
        "location": "Locatie",
        "locatie": "Locatie",
        "standplaats: provincie": "Regio",
        "provincie": "Regio",
        "province": "Regio",
        "region": "Regio",
        "regio": "Regio",
        "bedrijf: branche": "SBI_Sector",
        "sector": "SBI_Sector",
        "sbi_sector": "SBI_Sector",
        "sbi code": "SBI_Code",
        "sbi_code": "SBI_Code",
        "sbi": "SBI_Code",
        "kvk_number": "KVK",
        "kvk": "KVK",
        "contactpersoon: voornaam": "Contact_Voornaam",
        "contact_voornaam": "Contact_Voornaam",
        "contactpersoon: achternaam": "Contact_Achternaam",
        "contact_achternaam": "Contact_Achternaam",
        "contactpersoon: e-mail": "Email",
        "e-mail": "Email",
        "email": "Email",
        "contactpersoon: telefoon": "Telefoon",
        "phone": "Telefoon",
        "telefoon": "Telefoon",
        "website": "Website",
        "url": "URL",
        "link": "URL",
        "salarisindicatie": "salarisindicatie",
        "score": "Score",
        "prioriteit": "Prioriteit",
        "functie_type": "Functie_Type",
    }

    def __init__(self, path: Path, log: logging.Logger):
        self.path = path
        self.log = log

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            raise FileNotFoundError(
                f"Scraper output not found at {self.path}. "
                "Run the scraper first or set VACANCIES_INPUT_PATH."
            )
        if self.path.suffix.lower() in {".xlsx", ".xls"}:
            return self._load_excel()
        return self._load_json()

    def _load_json(self) -> list[dict[str, Any]]:
        with self.path.open(encoding="utf-8") as f:
            vacancies = json.load(f)
        self.log.info("Loaded %d vacancies from JSON %s", len(vacancies), self.path)
        return vacancies

    def _read_excel_autoheader(self) -> "pd.DataFrame":
        """Try header rows 0..5, pick the one yielding the most known columns."""
        best_df = None
        best_score = -1
        best_header = 0
        known_aliases = set(self.RAW_ALIASES.keys())
        for header_row in range(6):
            try:
                df = pd.read_excel(self.path, header=header_row)
            except Exception:
                continue
            if df.empty:
                continue
            cols_lower = {str(c).lower().strip() for c in df.columns}
            score = len(cols_lower & known_aliases)
            if score > best_score:
                best_score = score
                best_df = df
                best_header = header_row
        if best_df is None:
            return pd.read_excel(self.path)
        if best_header > 0:
            self.log.info("Auto-detected header on row %d (matched %d known columns)", best_header, best_score)
        return best_df

    def _normalize_columns(self, df: "pd.DataFrame") -> "pd.DataFrame":
        """Lowercase + apply RAW_ALIASES so both raw and processed exports work."""
        df.columns = [str(c).lower().strip() for c in df.columns]
        rename_map = {col: self.RAW_ALIASES[col] for col in df.columns if col in self.RAW_ALIASES}
        if rename_map:
            df = df.rename(columns=rename_map)
        return df

    def _load_excel(self) -> list[dict[str, Any]]:
        df = self._read_excel_autoheader()
        df = self._normalize_columns(df)
        vacancies: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            vacancy: dict[str, Any] = {}
            for excel_col, v3_field in self.JOBDIGGER_COLUMN_MAP.items():
                if excel_col not in df.columns:
                    continue
                val = row[excel_col]
                if pd.isna(val):
                    continue
                vacancy[v3_field] = str(val).strip() if isinstance(val, str) else val
            if vacancy.get("company"):
                vacancies.append(vacancy)
        self.log.info("Loaded %d vacancies from Excel %s", len(vacancies), self.path)
        return vacancies


# ---------------------------------------------------------------------------
# Stage 2: ICP filter — uses JobDigger's pre-computed Score column
# ---------------------------------------------------------------------------


class ICPFilter:
    """ICP filter based on lemlist_icp_audit.py (validated source of truth).

    Score = 50 base, max 100. Excluded keywords/SBI return 0 (immediate reject).
    Threshold default 75 (covers preferred SBI + regio OR preferred SBI + sector).

    Gates applied in order:
    1. EXCLUDED_KEYWORDS in company name → score 0 (overheid, zorg, uitzend, etc.)
    2. EXCLUDED_SBI ranges → score 0 (IT, finance, government, healthcare, retail)
    3. Base 50 + bonuses:
       - +20 PREFERRED_SBI (manufacturing, bouw, transport, energy)
       - +10 PREFERRED_REGIO (south/east NL provinces + cities)
       - +15 ICP_SECTORS (bouw, installatie, techniek, etc.)
    4. Has valid contact email
    """

    EXCLUDED_KEYWORDS = [
        "gemeente", "provincie", "ziekenhuis", "zorg", "onderwijs",
        "school", "universiteit", "hogeschool", "uitzend", "detach",
        "recruitment", "staffing", "interim", "overheid", "rijksoverheid",
        "waterschap", "uitleenbureau", "payroll",
    ]

    # Agency/intermediair e-maildomeinen: de vacature staat op naam van een echt
    # bedrijf, maar het contactadres is van een uitzend-/recruitmentbureau dat de
    # werving doet (bijv. ...@randstadprofessional.nl). Die mailen = onze dienst aan
    # een concurrent pitchen. Generieke keywords (V1 RECRUITMENT_DOMAIN_KEYWORDS) +
    # merknamen (de schakel die V1 miste).
    AGENCY_EMAIL_DOMAINS = [
        "recruitment", "uitzend", "detach", "staffing", "werving", "interim",
        "headhunt", "jobsolutions",
        "randstad", "tempo-team", "tempoteam", "adecco", "manpower", "olympia",
        "youngcapital", "startpeople", "start-people", "yacht", "brunel", "huxley",
        "synsel", "usg", "hays", "luba", "timing", "driessen", "continu", "maandag",
        "covebo", "actiefwerkt", "tence", "bmc.nl", "westerhof",
    ]

    # Competitor/uitzendbureau op BEDRIJFSNAAM (V1 COMPETITOR_PATTERNS, word-boundary).
    COMPETITOR_NAME_PATTERNS = [
        r"\b(uitzend|detacher|detachering|interim|staffing|payroll)\b",
        r"\b(recruitment|recruiter|werving\s*&?\s*selectie|w&s)\b",
        r"\b(hr\s*services|hr\s*solutions|human\s*capital|personnel)\b",
        r"\b(randstad|manpower|adecco|tempo\s*team|olympia|start\s*people)\b",
        r"\b(yacht|brunel|huxley|synsel|usn|youngcapital)\b",
    ]

    # Technische bedrijven die per ongeluk op een competitor-patroon matchen blijven.
    TECHNICAL_EXEMPTIONS = [
        "koeltechniek", "klimaattechniek", "installatietechniek",
        "elektrotechniek", "procestechniek", "milieutechniek",
    ]

    EXCLUDED_VACANCY_KEYWORDS = [
        # Stages / internships / weekend / volunteer
        "stage", "stagiair", "afstudeer", "leerling", "bbl", "internship",
        "vrijwilliger", "vrijwilligerswerk",
        "weekend", "zaterdaghulp", "vakantiekracht", "bijbaan", "scholier",
        "oproepkracht", "invalkracht", "bijbaantje",
        # Finance / admin / secretarial
        "accounting", "accountant", "boekhouder", "boekhouding",
        "administratief", "administratie", "receptionist", "secretaresse",
        "office manager", "management assistent", "assistent manager",
        "controller", "fiscalist",
        # Retail / hospitality / personal services
        "kassamedewerker", "verkoper", "verkoopmedewerker", "winkelmedewerker",
        "filiaalmanager", "winkelbediende",
        "kapper", "haarstylist", "schoonheidsspecialist", "stylist", "barber",
        "kok", "chef-kok", "keukenhulp", "afwasser", "bediening",
        "horeca", "hotelmedewerker", "restaurant",
        "autopoetser",
        # Sales / marketing / communications (commercial roles)
        "sales manager", "account manager", "accountmanager",
        "marketeer", "marketing", "content", "social media", "communicatie",
        "communication", "pr manager", "commercieel medewerker",
        "enterprise sales", "business development",
        # HR / coaching / training (non-recruitment)
        "hr adviseur", "hr medewerker", "hr assistent", "p&o medewerker",
        "coach", "trainer",
        # Service / hulp (low-skill)
        "klantenservice", "hulpkracht", "schoonmaker", "schoonmaak",
        # Creative (not engineering)
        "vormgever", "graphic designer", "creative",
        # Healthcare / education / social (uitzondering: techn. docent)
        "verpleegkundige", "verzorgende", "psycholog", "psychiat",
        "pedagog", "docent", "leerkracht", "lerar", "onderwijz",
        "tandarts", "fysio", "dietist", "huisarts",
        # Real estate / legal
        "vastgoed", "real estate", "jurist", "juridisch",
        # Driver / logistics (low-skill)
        "chauffeur", "heftruckchauffeur", "bezorger",
        # Cleaning / facility / outdoor gardening
        "facilitair", "conciërge",
        "groenvoorziening", "landschapsverzorging", "hovenier",
        "voorman groen", "uitvoerder groen", "groenmedewerker",
        # IT / software roles (excluded sector)
        "ict system engineer", "software developer", "software engineer",
        "fullstack", "backend developer", "frontend developer",
        "data scientist", "data analyst",
        # Training/coaching coordination
        "planningscoördinator training", "training coördinator",
    ]

    # Positive filter: vacancy title MUST match one of these keywords (technical roles)
    REQUIRED_VACANCY_KEYWORDS = [
        # Monteur family
        "monteur", "installateur", "fitter", "mechanic",
        "servicemonteur", "elektromonteur", "installatiemonteur",
        "field service",
        # Technicus / Engineer
        "technicus", "technician", "engineer", "ingenieur", "engineering",
        "medewerker technische dienst", "mtd",
        # Werkvoorbereiding / Calculatie
        "werkvoorbereider", "calculator", "kostendeskundige", "estimator",
        "cost engineer", "wvb",
        # Tekenen / Constructie
        "tekenaar", "constructeur", "designer", "cad", "drafter",
        # Project management
        "projectleider", "projectmanager", "project manager", "project leader",
        "uitvoerder", "werkvoorbereider",
        # PLC / Automation
        "plc", "automation", "scada", "dcs", "besturingstechnicus",
        # Teamleader / Coordinatie
        "teamleider", "team leader", "voorman", "shift leader", "shiftleader",
        "coordinator", "coördinator",
        # Inkoop / Procurement (technical)
        "inkoop", "inkoper", "procurement", "contract manager",
        # Production / Workshop
        "productieleider", "productiemanager", "werkplaats",
        "materieelbeheerder",
    ]

    # Conditional keywords: count ONLY if company is in a tech sector or preferred SBI.
    # Without sector context these are too generic ("manager", "lead") and would let
    # non-technical leadership roles through.
    CONDITIONAL_VACANCY_KEYWORDS = [
        "manager", "head of", "director", "lead", "leider",
        "adviseur", "advisor", "consultant", "specialist",
        "supervisor", "chef", "hoofd",
    ]

    EXCLUDED_SBI = [
        (6200, 6299), (6300, 6399),
        (6400, 6499), (6500, 6599),
        (8400, 8499), (8500, 8599),
        (8600, 8699), (8700, 8799), (8800, 8899),
        (7810, 7819), (7820, 7829), (7830, 7839),
        (7000, 7010), (7020, 7022),
        (4700, 4799),
        (7210, 7219),
    ]

    PREFERRED_SBI = [
        (2000, 3399),
        (4100, 4399),
        (4900, 5199),
        (3500, 3599),
    ]

    PREFERRED_REGIO = [
        "gelderland", "overijssel", "noord-brabant", "limburg", "utrecht",
        "arnhem", "nijmegen", "eindhoven", "tilburg", "apeldoorn",
        "enschede", "zwolle", "deventer", "doetinchem", "winterswijk",
    ]

    ICP_SECTORS = [
        "bouw", "installatie", "techniek", "industrie", "energie",
        "metaal", "logistiek", "transport", "infra", "food", "maritiem",
    ]

    DEFAULT_MIN_SCORE = 65

    def __init__(self, log: logging.Logger, min_score: int = DEFAULT_MIN_SCORE):
        self.log = log
        self.min_score = min_score

    def passes(self, vacancy: dict[str, Any]) -> bool:
        return self._compute_score(vacancy) >= self.min_score and self._email_gate(vacancy)

    def filter(self, vacancies: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        vacancies_list = list(vacancies)
        scored = [(v, self._compute_score(v)) for v in vacancies_list]
        qualified = [v for v, s in scored if s >= self.min_score and self._email_gate(v)]
        qualified.sort(key=lambda v: self._compute_score(v), reverse=True)

        # Diagnostic counts
        excluded_keyword = sum(1 for v, s in scored if s == 0 and self._has_excluded_keyword(v))
        agency_email = sum(1 for v, s in scored if s == 0 and not self._has_excluded_keyword(v) and self._is_agency_email(v))
        competitor = sum(1 for v, s in scored if s == 0 and not self._has_excluded_keyword(v) and not self._is_agency_email(v) and self._is_competitor_name(v))
        excluded_sbi = sum(1 for v, s in scored if s == 0 and not self._has_excluded_keyword(v) and not self._is_agency_email(v) and not self._is_competitor_name(v) and self._has_excluded_sbi(v))
        no_email = sum(1 for v, s in scored if s >= self.min_score and not self._email_gate(v))

        self.log.info(
            "ICP qualified: %d/%d (min_score=%d) | rejected: %d keyword, %d SBI, %d agency-email, %d competitor-naam, %d no-email",
            len(qualified), len(vacancies_list), self.min_score,
            excluded_keyword, excluded_sbi, agency_email, competitor, no_email,
        )
        return qualified

    def _compute_score(self, v: dict[str, Any]) -> int:
        """Scoring: exclusions return 0, otherwise base 50 + bonuses (max 100).

        Hard rejects (return 0): excluded company keyword, excluded vacancy keyword,
        excluded SBI. The required-vacancy keyword is now a +10 bonus (was hard gate)
        so industrial roles like "Operator C" at a manufacturer can still qualify
        via sector+SBI+regio combination.
        """
        if self._has_excluded_keyword(v):
            return 0
        if self._has_excluded_vacancy_keyword(v):
            return 0
        if self._is_agency_email(v):
            return 0
        if self._is_competitor_name(v):
            return 0
        if self._has_excluded_sbi(v):
            return 0
        score = 50
        if self._has_preferred_sbi(v):
            score += 20
        if self._has_preferred_regio(v):
            score += 10
        if self._has_icp_sector(v):
            score += 15
        if self._has_required_vacancy_keyword(v):
            score += 10  # bonus for explicit technical role title
        return min(score, 100)

    def _has_required_vacancy_keyword(self, v: dict[str, Any]) -> bool:
        title = str(v.get("title") or "").lower()
        if any(kw in title for kw in self.REQUIRED_VACANCY_KEYWORDS):
            return True
        # Conditional keywords only count when company is clearly in a tech sector
        if any(kw in title for kw in self.CONDITIONAL_VACANCY_KEYWORDS):
            return self._has_preferred_sbi(v) or self._has_icp_sector(v)
        return False

    def _has_excluded_keyword(self, v: dict[str, Any]) -> bool:
        company = str(v.get("company") or "").lower()
        return any(kw in company for kw in self.EXCLUDED_KEYWORDS)

    def _has_excluded_vacancy_keyword(self, v: dict[str, Any]) -> bool:
        title = str(v.get("title") or "").lower()
        return any(kw in title for kw in self.EXCLUDED_VACANCY_KEYWORDS)

    def _is_agency_email(self, v: dict[str, Any]) -> bool:
        """Contact-e-mail is van een uitzend-/recruitmentbureau (domein-match)."""
        email = str(v.get("contact_email") or "").lower()
        if "@" not in email:
            return False
        domain = email.split("@", 1)[1]
        return any(kw in domain for kw in self.AGENCY_EMAIL_DOMAINS)

    def _is_competitor_name(self, v: dict[str, Any]) -> bool:
        """Bedrijfsnaam is een uitzendbureau/concurrent (regex, met techniek-uitzondering)."""
        company = str(v.get("company") or "").lower()
        if not company:
            return False
        if any(tech in company for tech in self.TECHNICAL_EXEMPTIONS):
            return False
        return any(re.search(p, company) for p in self.COMPETITOR_NAME_PATTERNS)

    def _sbi_int(self, v: dict[str, Any]) -> int | None:
        """Parse + normalize SBI code to level-3 (4-digit) for range matching.

        JobDigger may store SBI as 2-digit (27), 3-digit (271), 4-digit (2711),
        or 5-6-digit (27110, 711203). We normalize to 4-digit:
          - 2 digit -> ×100  (27 -> 2700)
          - 3 digit -> ×10   (271 -> 2710)
          - 4 digit -> as-is (2711)
          - 5+ digit -> truncate to first 4 (70221 -> 7022, 711203 -> 7112)
        This lets range checks like (7020, 7022) match 70221 correctly.
        """
        sbi_raw = v.get("sbi_code")
        if sbi_raw is None or (isinstance(sbi_raw, float) and sbi_raw != sbi_raw):
            return None
        try:
            code = int(float(str(sbi_raw)))
        except (TypeError, ValueError):
            return None
        if code < 100:
            code = code * 100
        elif code < 1000:
            code = code * 10
        elif code >= 10000:
            # Truncate to 4 digits: 70221 -> 7022, 711203 -> 7112
            while code >= 10000:
                code = code // 10
        return code

    def _has_excluded_sbi(self, v: dict[str, Any]) -> bool:
        sbi = self._sbi_int(v)
        if sbi is None:
            return False
        return any(lo <= sbi <= hi for lo, hi in self.EXCLUDED_SBI)

    def _has_preferred_sbi(self, v: dict[str, Any]) -> bool:
        sbi = self._sbi_int(v)
        if sbi is None:
            return False
        return any(lo <= sbi <= hi for lo, hi in self.PREFERRED_SBI)

    def _has_preferred_regio(self, v: dict[str, Any]) -> bool:
        location_fields = [v.get("location"), v.get("region")]
        haystack = " ".join(str(x) for x in location_fields if x).lower()
        return any(r in haystack for r in self.PREFERRED_REGIO)

    def _has_icp_sector(self, v: dict[str, Any]) -> bool:
        sector = str(v.get("sector") or "").lower()
        return any(s in sector for s in self.ICP_SECTORS)

    def _email_gate(self, v: dict[str, Any]) -> bool:
        email = str(v.get("contact_email") or "").strip()
        return "@" in email and email.lower() not in {"nan", "none", ""}


# ---------------------------------------------------------------------------
# Stage 2b: Deduplication (Lemlist graveyard + cross-campaign history)
# ---------------------------------------------------------------------------


class Deduplicator:
    """Cross-campaign + graveyard dedup.

    Fetches at startup:
    - Lemlist unsubscribe/graveyard list (live from API)
    - All leads across known campaigns (V3 + P12 + P13 + P14)

    Filters out vacancies whose contact_email matches either set.
    """

    # All historic campaigns to check (from CLAUDE.md memory + lemlist-api.md)
    HISTORIC_CAMPAIGNS = [
        "cam_B3BDF7MeBCcTN3CtS",  # V3 P12 (current)
        "cam_8KGpG2G5ppSrwy6v4",  # P12 Stage 2
        "cam_rkPQbJ8w7QbAkWSGJ",  # P13 ICP Top
        "cam_mB5MTdo9CWCsCrLfw",  # P14 Corporate Recruiter
    ]

    def __init__(self, cfg: "Config", log: logging.Logger):
        self.cfg = cfg
        self.log = log
        self.blocked_emails: set[str] = set()

    def load_blocklist(self) -> None:
        """Fetch graveyard + historic leads from Lemlist API."""
        graveyard = self._fetch_graveyard()
        historic = self._fetch_historic_leads()
        self.blocked_emails = graveyard | historic
        self.log.info(
            "Dedup blocklist loaded: %d graveyard + %d historic = %d total emails",
            len(graveyard), len(historic), len(self.blocked_emails),
        )

    def _fetch_graveyard(self) -> set[str]:
        """GET /unsubscribes — all blocked emails Lemlist-wide."""
        emails: set[str] = set()
        try:
            response = requests.get(
                "https://api.lemlist.com/api/unsubscribes",
                auth=("", self.cfg.lemlist_api_key),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            for item in data if isinstance(data, list) else data.get("unsubscribes", []):
                email = (item.get("value") or item.get("email") or "").lower().strip()
                if email:
                    emails.add(email)
        except Exception as e:
            self.log.warning("Failed to fetch Lemlist graveyard: %s", e)
        return emails

    def _fetch_historic_leads(self) -> set[str]:
        """List all leads across historic campaigns to prevent re-mailing.

        Note: Lemlist /leads endpoint returns lead_id + contactId but not email
        directly. We rely on Lemlist's own "already in campaign" rejection
        on POST instead of pre-fetching N+1 contact details.
        """
        return set()  # Lemlist API handles cross-campaign rejection automatically

    def is_blocked(self, email: str) -> bool:
        if not email:
            return False
        return email.lower().strip() in self.blocked_emails

    def filter(self, vacancies: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        filtered = [v for v in vacancies if not self.is_blocked(v.get("contact_email") or "")]
        rejected = len(list(vacancies)) - len(filtered) if isinstance(vacancies, list) else 0
        if rejected > 0:
            self.log.info("Dedup: rejected %d leads already in graveyard/history", rejected)
        return filtered


# ---------------------------------------------------------------------------
# Stage 3: Claude distill prompts
# ---------------------------------------------------------------------------


class PromptExecutor:
    """Runs the vacature and doelgroep distills via the Anthropic API.

    Uses prompt caching on the system prompt so each lead in the daily
    batch hits the cache after the first request.
    """

    def __init__(self, cfg: Config, log: logging.Logger):
        self.cfg = cfg
        self.log = log
        self.client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
        self.vacature_prompt = (PROMPTS_DIR / "vacature_distill.md").read_text(encoding="utf-8")
        self.doelgroep_prompt = (PROMPTS_DIR / "doelgroep_distill.md").read_text(encoding="utf-8")

    def vacature(self, vacancy: dict[str, Any]) -> dict[str, Any]:
        return self._run(self.vacature_prompt, vacancy, kind="vacature")

    def doelgroep(self, vacancy: dict[str, Any]) -> dict[str, Any]:
        return self._run(self.doelgroep_prompt, vacancy, kind="doelgroep")

    def _run(self, system_prompt: str, vacancy: dict[str, Any], kind: str) -> dict[str, Any]:
        user_payload = json.dumps(vacancy, ensure_ascii=False, indent=2)
        response = self.client.messages.create(
            model=self.cfg.claude_model,
            max_tokens=8000,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_payload}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            self.log.warning("%s distill returned non-JSON; wrapping as raw", kind)
            return {"raw": text}


# ---------------------------------------------------------------------------
# Stage 4: PDF rendering
# ---------------------------------------------------------------------------


class PDFGenerator:
    def __init__(self, output_dir: Path, log: logging.Logger):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log = log
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(self, template_name: str, context: dict[str, Any], filename: str) -> Path:
        html = self.env.get_template(template_name).render(**context)
        out_path = self.output_dir / filename
        HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf(str(out_path))
        return out_path


# ---------------------------------------------------------------------------
# Stage 5: Supabase storage
# ---------------------------------------------------------------------------


class StorageManager:
    def __init__(self, cfg: Config, log: logging.Logger):
        self.cfg = cfg
        self.log = log
        self.client: Client = create_client(cfg.supabase_url, cfg.supabase_key)

    def upload(self, local_path: Path, remote_name: str) -> str:
        with local_path.open("rb") as f:
            self.client.storage.from_(self.cfg.supabase_bucket).upload(
                path=remote_name,
                file=f,
                file_options={"content-type": "application/pdf", "upsert": "true"},
            )
        return self.client.storage.from_(self.cfg.supabase_bucket).get_public_url(remote_name)


# ---------------------------------------------------------------------------
# Stage 6: Lemlist
# ---------------------------------------------------------------------------


class LemlistUploader:
    API_BASE = "https://api.lemlist.com/api"

    def __init__(self, cfg: Config, log: logging.Logger):
        self.cfg = cfg
        self.log = log

    def add_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.API_BASE}/campaigns/{self.cfg.lemlist_campaign_id}/leads/{lead['email']}"
        response = requests.post(
            url,
            auth=("", self.cfg.lemlist_api_key),
            json=lead,
            timeout=30,
        )
        if response.status_code == 400:
            error_text = response.text.lower()
            # Graveyard/unsubscribed = terminal, never retry
            if any(variant in error_text for variant in ["graveyard", "unsubscribed"]):
                self.log.info(f"Lead {lead['email']} skipped (unsubscribed): {response.text[:100]}")
                return {"_id": f"skipped-{lead['email']}", "status": "unsubscribed"}
            # Already in campaign = update existing lead with new PDF URLs
            if any(variant in error_text for variant in ["already", "exists", "duplicate"]):
                self.log.info(f"Lead {lead['email']} exists — updating with new fields")
                return self._update_lead(lead)
            # Other 400 errors are fatal — log and raise
            try:
                error_detail = response.json()
                self.log.error(f"Lemlist 400 error for {lead['email']}: {error_detail}")
            except:
                self.log.error(f"Lemlist 400 error for {lead['email']} (no JSON body): {response.text}")
            response.raise_for_status()
        elif response.status_code >= 400:
            self.log.error(f"Lemlist API error {response.status_code} for {lead['email']}: {response.text[:200]}")
            response.raise_for_status()

        return response.json()

    def _update_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        """PATCH an existing lead to refresh custom fields (PDF URLs etc).

        Lemlist rate-limit: 1 req/12s. Wait before PATCH after POST.
        Retry once on 429 with longer backoff.
        """
        url = f"{self.API_BASE}/campaigns/{self.cfg.lemlist_campaign_id}/leads/{lead['email']}"
        time.sleep(13)  # rate-limit buffer after the failed POST

        for attempt in (1, 2):
            response = requests.patch(
                url,
                auth=("", self.cfg.lemlist_api_key),
                json=lead,
                timeout=30,
            )
            if response.status_code == 429 and attempt == 1:
                self.log.info(f"Lemlist 429 on PATCH, backing off 90s before retry")
                time.sleep(90)
                continue
            if response.status_code >= 400:
                self.log.warning(f"Lemlist PATCH failed for {lead['email']} ({response.status_code}): {response.text[:200]}")
                return {"_id": f"update-failed-{lead['email']}", "status": "update_failed"}
            self.log.info(f"Lead {lead['email']} updated with new fields")
            result = response.json() if response.text else {}
            result["status"] = "updated"
            return result
        return {"_id": f"update-failed-{lead['email']}", "status": "update_failed"}


# ---------------------------------------------------------------------------
# Slack notifier
# ---------------------------------------------------------------------------


def notify_slack(webhook: str | None, text: str) -> None:
    if not webhook:
        return
    try:
        requests.post(webhook, json={"text": text}, timeout=10)
    except requests.RequestException:
        pass


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


@dataclass
class RunStats:
    started: float = field(default_factory=time.monotonic)
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    def elapsed(self) -> float:
        return time.monotonic() - self.started


def slugify(value: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in value).strip("_").lower()


# Freemail-domeinen: hier NIET op domein dedupen (anders vallen losse personen samen).
FREEMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "hotmail.com", "hotmail.nl", "outlook.com",
    "live.nl", "live.com", "icloud.com", "me.com", "ziggo.nl", "kpnmail.nl",
    "telfort.nl", "planet.nl", "home.nl", "xs4all.nl", "yahoo.com", "casema.nl",
}


def collapse_by_company(vacancies: list[dict[str, Any]], log: logging.Logger) -> list[dict[str, Any]]:
    """Houd max. 1 vacature per organisatie.

    De input is al op ICP-score gesorteerd (hoog->laag), dus de eerste die we
    per organisatie zien is de best scorende. Dedup op:
      - bedrijfsnaam, en
      - volledige contact-email, en
      - e-maildomein (vangt multi-vestiging zoals Breman Kampen/Zwolle @breman.nl;
        freemail-domeinen uitgezonderd om losse personen niet samen te voegen).
    """
    seen_company: set[str] = set()
    seen_email: set[str] = set()
    seen_domain: set[str] = set()
    out: list[dict[str, Any]] = []
    dropped = 0
    for v in vacancies:
        company = (v.get("company") or "").strip().lower()
        email = (v.get("contact_email") or "").strip().lower()
        domain = email.split("@", 1)[1] if "@" in email else ""
        dom_key = domain if domain and domain not in FREEMAIL_DOMAINS else ""
        if ((company and company in seen_company)
                or (email and email in seen_email)
                or (dom_key and dom_key in seen_domain)):
            dropped += 1
            continue
        if company:
            seen_company.add(company)
        if email:
            seen_email.add(email)
        if dom_key:
            seen_domain.add(dom_key)
        out.append(v)
    log.info(
        "Company-dedup: %d organisaties (best scorende vacature elk) | %d dubbele samengevoegd",
        len(out), dropped,
    )
    return out


def process_lead(
    vacancy: dict[str, Any],
    prompts: PromptExecutor,
    pdfgen: PDFGenerator,
    storage: StorageManager,
    lemlist: LemlistUploader,
    log: logging.Logger,
    dry_run: bool = False,
    canary_email: str | None = None,
) -> dict[str, Any]:
    lead_id = vacancy.get("id") or slugify(
        f"{vacancy.get('company', 'unknown')}_{vacancy.get('title', 'role')}"
    )

    vacature_data = prompts.vacature(vacancy)
    doelgroep_data = prompts.doelgroep(vacancy)

    dim_labels = {
        "vacaturetitel_vindbaarheid": "Vacaturetitel vindbaarheid",
        "functieomschrijving": "Functieomschrijving",
        "salaris_arbeidsvoorwaarden": "Salaris & arbeidsvoorwaarden",
        "employer_branding": "Employer branding",
        "kandidaat_experience": "Kandidaat experience",
        "kanaalstrategie": "Kanaalstrategie",
        "concurrentiekracht": "Concurrentiekracht",
        "seo_online_vindbaarheid": "SEO online vindbaarheid",
    }

    meta = {
        "bedrijf": vacancy.get("company", ""),
        "bedrijf_slug": slugify(vacancy.get("company", "")),
        "functietitel": vacancy.get("title", ""),
        "niveau": vacancy.get("seniority", ""),
        "regio": vacancy.get("location", ""),
        "sector": vacancy.get("sector", ""),
    }

    touch1_context = {"vacancy": vacancy, "meta": meta, "dim_labels": dim_labels, **vacature_data}
    touch2_context = {"vacancy": vacancy, "meta": meta, "dim_labels": dim_labels, **doelgroep_data}

    touch1_pdf = pdfgen.render(
        "touch1_vacature.html",
        touch1_context,
        f"{lead_id}_touch1_vacature.pdf",
    )
    touch2_pdf = pdfgen.render(
        "touch2_doelgroep.html",
        touch2_context,
        f"{lead_id}_touch2_doelgroep.pdf",
    )

    if dry_run:
        touch1_url = f"(DRY-RUN) {touch1_pdf}"
        touch2_url = f"(DRY-RUN) {touch2_pdf}"
        log.info("[%s] DRY-RUN: PDFs generated at %s, %s", lead_id, touch1_pdf, touch2_pdf)
        lemlist_result = {"_id": f"dry-run-{lead_id}", "status": "dry-run"}
    else:
        touch1_url = storage.upload(touch1_pdf, f"{lead_id}/touch1_vacature.pdf")
        touch2_url = storage.upload(touch2_pdf, f"{lead_id}/touch2_doelgroep.pdf")
        lead_email = canary_email or (vacancy.get("contact_email") or f"hr@{vacancy.get('company_domain', 'example.com')}")

        # Per-lead copy variables (uit de twee distill-outputs) — met veilige defaults.
        vac_kpi = vacature_data.get("kpi", {})
        dg_h = doelgroep_data.get("hoogtepunten_pag1", {})
        dg_conc = doelgroep_data.get("marktdruk_index", {}).get("top_concurrent", {})
        # Role-mailbox flag (info@/hr@/recruitment@/...) — alleen taggen, niet skippen.
        _local = (lead_email.split("@", 1)[0] or "").lower()
        is_role_inbox = any(_local.startswith(p) for p in
                            ("hr", "info", "recruitment", "recruiting", "sollicit", "vacature", "jobs", "career"))

        lead_payload = {
            "email": lead_email,
            "firstName": vacancy.get("contact_first_name", "") or "",  # leeg => Lemlist |fallback werkt
            "lastName": vacancy.get("contact_last_name", "") or "",
            "companyName": vacancy.get("company", "") or "Unknown",
            "jobTitle": vacancy.get("title", "") or "Role",
            "city": vacancy.get("location", "") or "",
            "vacaturePdfUrl": touch1_url,
            "doelgroepPdfUrl": touch2_url,
            # --- per-lead copy variabelen (touch 1-4) ---
            "vacatureScore": str(vacature_data.get("score_totaal", "")),
            "sterksteDimensie": (vacature_data.get("sterkste_punt") or {}).get("label", ""),
            "zwaksteDimensie": (vacature_data.get("zwakste_punt") or {}).get("label", ""),
            "aanbodVraag": vac_kpi.get("aanbod_vraag_ratio", ""),
            "schaarste": (doelgroep_data.get("kpi") or {}).get("schaarste_label", ""),
            "topKanaal": (dg_h.get("top_kanaal") or {}).get("naam", ""),
            "salarisMedior": (dg_h.get("salaris_medior") or {}).get("bedrag", ""),
            "topConcurrent": dg_conc.get("naam", ""),
            "concurrentPremie": dg_conc.get("salarispremie", ""),
            # --- segmentatie/QA ---
            "isRoleInbox": "true" if is_role_inbox else "false",
        }
        lemlist_result = lemlist.add_lead(lead_payload)

    log.info("[%s] processed -> lemlist id=%s", lead_id, lemlist_result.get("_id", "n/a"))
    return lemlist_result


def run() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip Supabase/Lemlist uploads, local PDFs only")
    args = parser.parse_args()

    cfg = Config.from_env()
    log = setup_logging(cfg.log_dir)
    mode = "DRY-RUN" if args.dry_run else "LIVE"
    canary_note = f" (CANARY → {cfg.canary_email})" if cfg.canary_email else ""
    log.info("JobDigger V3 daily run starting [%s]%s (model=%s, batch=%d)", mode, canary_note, cfg.claude_model, cfg.lead_batch_size)

    loader = VacancyLoader(cfg.vacancies_path, log)
    icp = ICPFilter(log, min_score=cfg.min_icp_score)
    dedup = Deduplicator(cfg, log)
    prompts = PromptExecutor(cfg, log)
    pdfgen = PDFGenerator(cfg.pdf_dir, log)
    storage = StorageManager(cfg, log)
    lemlist = LemlistUploader(cfg, log)

    vacancies = loader.load()
    qualified = icp.filter(vacancies)
    dedup.load_blocklist()
    deduplicated = dedup.filter(qualified)
    collapsed = collapse_by_company(deduplicated, log)
    offset = int(os.environ.get("LEAD_OFFSET", "0"))
    selected = collapsed[offset: offset + cfg.lead_batch_size]
    log.info("Selectie: offset=%d, batch=%d -> %d leads van %d beschikbaar", offset, cfg.lead_batch_size, len(selected), len(collapsed))

    stats = RunStats()
    for vacancy in selected:
        stats.processed += 1
        try:
            process_lead(vacancy, prompts, pdfgen, storage, lemlist, log, dry_run=args.dry_run, canary_email=cfg.canary_email)
            stats.succeeded += 1
        except Exception as exc:
            stats.failed += 1
            msg = f"{vacancy.get('id', '?')}: {exc!r}"
            stats.errors.append(msg)
            log.exception("Lead failed: %s", msg)

    summary = (
        f"JobDigger V3 [{mode}]: {stats.succeeded}/{stats.processed} leads OK "
        f"({stats.failed} failed) in {stats.elapsed():.1f}s"
    )
    log.info(summary)
    if not args.dry_run:
        notify_slack(cfg.slack_webhook_url, summary)
    return 0 if stats.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
