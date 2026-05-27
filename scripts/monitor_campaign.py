#!/usr/bin/env python3
"""Dagelijkse Lemlist-campagne monitor -> Slack, met bijstuur-drempels + reply-sentiment.

Hergebruikt ab_report.py voor de stats (sent/open/reply/click/bounce/unsub) en voegt toe:
  - Reply-sentiment (Claude Haiku op subject + messagePreview): interesse/vraag/bezwaar/afwijzing.
    LET OP: Lemlist geeft alleen een korte preview terug, geen volledige reply-tekst -> grove eerste pass.
  - Bijstuur-drempels (open/reply/bounce/unsub) -> concrete actie-flags.
  - Slack-post (SLACK_WEBHOOK_URL).

Gebruik:
  python scripts/monitor_campaign.py                 # alle activiteit -> Slack
  python scripts/monitor_campaign.py --since 2026-05-27
  python scripts/monitor_campaign.py --no-slack      # alleen stdout
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ab_report as ab  # noqa: E402  (hergebruik get/fetch/campaign/load_env/API)

# Bijstuur-drempels (rates in %); buiten deze grenzen -> actie-flag.
THRESHOLDS = {"open": 40.0, "reply": 5.0, "bounce": 5.0, "unsub": 2.0}
SENTIMENTS = ["interesse", "vraag", "bezwaar", "afwijzing", "overig"]
MONITOR_MODEL = "claude-haiku-4-5-20251001"


def fetch_reply_items(key: str, cid: str, since: datetime | None, cap: int = 60) -> list[dict]:
    """Haal ruwe emailsReplied-activiteiten op (subject + messagePreview + fromEmail)."""
    items, off = [], 0
    while len(items) < cap:
        r = ab.get(f"{ab.API}/activities", key,
                   params={"campaignId": cid, "type": "emailsReplied", "limit": 100, "offset": off})
        if r.status_code != 200:
            break
        batch = r.json()
        if not isinstance(batch, list) or not batch:
            break
        for a in batch:
            ts = a.get("createdAt") or ""
            if since and ts:
                try:
                    if datetime.fromisoformat(ts.replace("Z", "+00:00")) < since:
                        continue
                except ValueError:
                    pass
            items.append({"subject": a.get("subject", ""),
                          "preview": a.get("messagePreview", ""),
                          "from": a.get("fromEmail", "")})
        off += len(batch)
        if len(batch) < 100:
            break
    return items[:cap]


def classify_sentiment(items: list[dict], anthropic_key: str | None) -> dict:
    """Batch-classificeer replies in interesse/vraag/bezwaar/afwijzing/overig (1 Claude-call)."""
    counts = {s: 0 for s in SENTIMENTS}
    if not items or not anthropic_key:
        return counts
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        lines = [f'{i}. onderwerp="{x["subject"]}" preview="{x["preview"]}"' for i, x in enumerate(items)]
        prompt = (
            "Classificeer elke e-mail-reply in PRECIES EEN label: "
            "interesse (positief/open voor gesprek), vraag (wil meer info), "
            "bezwaar (twijfel/voorwaarde), afwijzing (geen interesse/uitschrijven), overig.\n"
            "Antwoord ALLEEN met een JSON-array van labels in dezelfde volgorde, bijv. "
            '["interesse","afwijzing"].\n\nReplies:\n' + "\n".join(lines)
        )
        resp = client.messages.create(
            model=MONITOR_MODEL, max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        text = text[text.find("["): text.rfind("]") + 1]
        for label in json.loads(text):
            label = str(label).lower().strip()
            counts[label if label in counts else "overig"] += 1
    except Exception as e:  # classificatie is best-effort, nooit blokkerend
        counts["_error"] = str(e)[:120]
    return counts


def steering_flags(r: dict) -> list[str]:
    """Concrete bijstuur-acties op basis van drempels."""
    sent = r["sent"] or 0
    if sent == 0:
        return ["ℹ️ Nog niets verzonden (campagne paused/draft) — start in Lemlist om te meten."]
    pct = lambda n: 100.0 * n / sent
    flags = []
    if pct(r["open"]) < THRESHOLDS["open"]:
        flags.append(f"📉 Open rate {pct(r['open']):.0f}% < {THRESHOLDS['open']:.0f}% → subjects A/B-testen + deliverability (SPF/DKIM/warm-up).")
    if pct(r["reply"]) < THRESHOLDS["reply"]:
        flags.append(f"📉 Reply rate {pct(r['reply']):.1f}% < {THRESHOLDS['reply']:.0f}% → opening/CTA aanscherpen, personalisatie.")
    if pct(r["bounce"]) > THRESHOLDS["bounce"]:
        flags.append(f"🚨 Bounce {pct(r['bounce']):.1f}% > {THRESHOLDS['bounce']:.0f}% → e-mailverificatie / lijstkwaliteit.")
    if pct(r["unsub"]) > THRESHOLDS["unsub"]:
        flags.append(f"⚠️ Unsub {pct(r['unsub']):.1f}% > {THRESHOLDS['unsub']:.0f}% → targeting/relevantie herzien.")
    return flags or ["✅ Alle rates binnen norm."]


def build_message(r: dict, sent_counts: dict, since_label: str) -> str:
    sent = r["sent"] or 0
    pct = lambda n: f"{100.0*n/sent:.1f}%" if sent else "—"
    lines = [
        f"*JobDigger V3 — campagne-monitor*{since_label}",
        f"`{r['name']}`",
        f"• Verzonden: *{sent}*",
        f"• Open: {r['open']} ({pct(r['open'])}) · Reply: {r['reply']} ({pct(r['reply'])}) · Clicks: {r['click']}",
        f"• Bounce: {r['bounce']} ({pct(r['bounce'])}) · Unsub: {r['unsub']} ({pct(r['unsub'])})",
    ]
    if sent and r["reply"]:
        sc = " · ".join(f"{k}:{v}" for k, v in sent_counts.items() if k in SENTIMENTS and v)
        lines.append(f"• Reply-sentiment: {sc or '—'}")
    lines.append("*Bijsturen:*")
    lines += [f"  {f}" for f in steering_flags(r)]
    return "\n".join(lines)


def post_slack(webhook: str | None, text: str) -> bool:
    if not webhook:
        return False
    try:
        return requests.post(webhook, json={"text": text}, timeout=10).status_code < 300
    except requests.RequestException:
        return False


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--since", help="ISO-datum (YYYY-MM-DD): tel alleen activiteit vanaf deze datum")
    p.add_argument("--no-slack", action="store_true", help="Alleen stdout, niet posten naar Slack")
    args = p.parse_args()
    since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc) if args.since else None

    env = ab.load_env()
    key = env["LEMLIST_API_KEY"]
    cid = env["LEMLIST_CAMPAIGN_ID"]
    anth = env.get("ANTHROPIC_API_KEY")
    webhook = env.get("SLACK_WEBHOOK_URL")

    r = ab.campaign(key, cid, since)
    replies = fetch_reply_items(key, cid, since) if r["reply"] else []
    sent_counts = classify_sentiment(replies, anth)

    since_label = f" (sinds {args.since})" if args.since else ""
    msg = build_message(r, sent_counts, since_label)
    print(msg)

    if not args.no_slack:
        ok = post_slack(webhook, msg)
        print(f"\n[slack] {'gepost ✓' if ok else 'niet gepost (geen webhook / fout)'}")


if __name__ == "__main__":
    main()
