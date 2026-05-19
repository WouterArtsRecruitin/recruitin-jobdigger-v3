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
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import anthropic
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
    canary_email: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()

        def required(name: str) -> str:
            value = os.environ.get(name)
            if not value:
                raise RuntimeError(f"Missing required env var: {name}")
            return value

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
            vacancies_path=ROOT / os.environ.get(
                "VACANCIES_INPUT_PATH", "data/daily_vacancies.json"
            ),
            pdf_dir=ROOT / os.environ.get("PDF_OUTPUT_DIR", "storage/pdfs"),
            log_dir=ROOT / os.environ.get("LOG_DIR", "logs"),
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
    def __init__(self, path: Path, log: logging.Logger):
        self.path = path
        self.log = log

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            raise FileNotFoundError(
                f"Scraper output not found at {self.path}. "
                "Run the scraper first or set VACANCIES_INPUT_PATH."
            )
        with self.path.open(encoding="utf-8") as f:
            vacancies = json.load(f)
        self.log.info("Loaded %d vacancies from %s", len(vacancies), self.path)
        return vacancies


# ---------------------------------------------------------------------------
# Stage 2: ICP filter (6 binary gates)
# ---------------------------------------------------------------------------


class ICPFilter:
    """Binary 6-gate filter. A vacancy passes only if all gates return True.

    Gates are intentionally strict — we want ~15-20% pass-through on the
    daily 200-vacancy scrape, yielding ~20 qualified leads.
    """

    TARGET_SECTORS = {
        "oil & gas", "olie en gas", "energie",
        "bouw", "construction",
        "productie", "manufacturing", "industrie",
        "automation", "automatisering",
        "renewable", "wind", "solar", "duurzame energie",
    }

    def __init__(self, log: logging.Logger):
        self.log = log

    def passes(self, vacancy: dict[str, Any]) -> bool:
        gates = [
            self._gate_sector(vacancy),
            self._gate_seniority(vacancy),
            self._gate_location(vacancy),
            self._gate_contract(vacancy),
            self._gate_company_size(vacancy),
            self._gate_has_contact(vacancy),
        ]
        return all(gates)

    def filter(self, vacancies: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        qualified = [v for v in vacancies if self.passes(v)]
        self.log.info("ICP qualified: %d/%d", len(qualified), len(list(vacancies)) if isinstance(vacancies, list) else -1)
        return qualified

    def _gate_sector(self, v: dict[str, Any]) -> bool:
        sector = (v.get("sector") or v.get("industry") or "").lower()
        return any(target in sector for target in self.TARGET_SECTORS)

    def _gate_seniority(self, v: dict[str, Any]) -> bool:
        level = (v.get("seniority") or v.get("level") or "").lower()
        return level in {"medior", "senior", "lead", "principal", "expert"}

    def _gate_location(self, v: dict[str, Any]) -> bool:
        country = (v.get("country") or "").lower()
        return country in {"nl", "netherlands", "nederland", ""}

    def _gate_contract(self, v: dict[str, Any]) -> bool:
        contract = (v.get("contract_type") or v.get("employment") or "").lower()
        return contract in {"vast", "permanent", "fulltime", "full-time", ""}

    def _gate_company_size(self, v: dict[str, Any]) -> bool:
        size = v.get("company_size")
        if size is None:
            return True
        try:
            return int(size) >= 20
        except (TypeError, ValueError):
            return True

    def _gate_has_contact(self, v: dict[str, Any]) -> bool:
        return bool(v.get("contact_email") or v.get("company_domain"))


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
        """PATCH an existing lead to refresh custom fields (PDF URLs etc)."""
        url = f"{self.API_BASE}/campaigns/{self.cfg.lemlist_campaign_id}/leads/{lead['email']}"
        response = requests.patch(
            url,
            auth=("", self.cfg.lemlist_api_key),
            json=lead,
            timeout=30,
        )
        if response.status_code >= 400:
            self.log.warning(f"Lemlist PATCH failed for {lead['email']} ({response.status_code}): {response.text[:200]}")
            return {"_id": f"update-failed-{lead['email']}", "status": "update_failed"}
        self.log.info(f"Lead {lead['email']} updated with new fields")
        result = response.json() if response.text else {}
        result["status"] = "updated"
        return result


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
        lead_payload = {
            "email": lead_email,
            "firstName": vacancy.get("contact_first_name", "") or "Contact",
            "lastName": vacancy.get("contact_last_name", "") or "",
            "companyName": vacancy.get("company", "") or "Unknown",
            "jobTitle": vacancy.get("title", "") or "Role",
            "city": vacancy.get("location", "") or "",
            "vacaturePdfUrl": touch1_url,
            "doelgroepPdfUrl": touch2_url,
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
    icp = ICPFilter(log)
    prompts = PromptExecutor(cfg, log)
    pdfgen = PDFGenerator(cfg.pdf_dir, log)
    storage = StorageManager(cfg, log)
    lemlist = LemlistUploader(cfg, log)

    vacancies = loader.load()
    qualified = [v for v in vacancies if icp.passes(v)]
    log.info("ICP qualified: %d/%d", len(qualified), len(vacancies))
    selected = qualified[: cfg.lead_batch_size]

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
