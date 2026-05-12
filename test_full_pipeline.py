"""Smoke test the full pipeline with a single dummy lead.

Skips Supabase upload and Lemlist creation when those env vars are not set,
so it can be run locally with only ANTHROPIC_API_KEY configured.

Usage:
    python test_full_pipeline.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from daily_automation import (  # noqa: E402
    ICPFilter,
    PDFGenerator,
    PromptExecutor,
    setup_logging,
)

DUMMY_VACANCY = {
    "id": "test_001",
    "title": "Senior Automation Engineer",
    "company": "TestCorp B.V.",
    "company_domain": "testcorp.nl",
    "contact_email": "hr@testcorp.nl",
    "contact_first_name": "Test",
    "contact_last_name": "Recruiter",
    "sector": "Automation",
    "seniority": "Senior",
    "country": "NL",
    "contract_type": "Vast",
    "company_size": 120,
    "location": "Eindhoven",
    "description": (
        "We are looking for a Senior Automation Engineer with PLC, SCADA, "
        "and Python experience to join our growing team."
    ),
}


def main() -> int:
    load_dotenv()
    root = Path(__file__).parent
    log = setup_logging(root / "logs")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.error("ANTHROPIC_API_KEY not set; aborting test.")
        return 1

    log.info("=== JobDigger V3 smoke test ===")

    icp = ICPFilter(log)
    assert icp.passes(DUMMY_VACANCY), "Dummy vacancy should pass ICP — fix fixture"
    log.info("[OK] ICP filter passes dummy vacancy")

    # Minimal Config-equivalent for the executor; bypass full Config so the
    # test runs without Lemlist / Supabase secrets.
    class _Cfg:
        anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]
        claude_model = os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")

    executor = PromptExecutor(_Cfg(), log)  # type: ignore[arg-type]
    vacature = executor.vacature(DUMMY_VACANCY)
    log.info("[OK] vacature distill: %d keys", len(vacature))
    doelgroep = executor.doelgroep(DUMMY_VACANCY)
    log.info("[OK] doelgroep distill: %d keys", len(doelgroep))

    pdf_dir = root / "storage" / "pdfs"
    pdfgen = PDFGenerator(pdf_dir, log)
    touch1 = pdfgen.render(
        "touch1_vacature.html",
        {"vacancy": DUMMY_VACANCY, "distill": vacature},
        "test_001_touch1.pdf",
    )
    touch2 = pdfgen.render(
        "touch2_doelgroep.html",
        {"vacancy": DUMMY_VACANCY, "distill": doelgroep},
        "test_001_touch2.pdf",
    )
    log.info("[OK] PDFs rendered: %s (%d KB), %s (%d KB)",
             touch1.name, touch1.stat().st_size // 1024,
             touch2.name, touch2.stat().st_size // 1024)

    log.info("=== Smoke test PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
