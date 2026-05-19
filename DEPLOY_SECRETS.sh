#!/usr/bin/env bash
# JobDigger V3 — GitHub Secrets prep script
#
# Per-secret per-destination flow. Lees elke regel, voer handmatig uit.
# Bedoeling: TRANSPARANT — geen autonoom set, jij ziet welke value waar heen gaat.
#
# Voer NOOIT dit hele script in één keer uit. Run regel voor regel.
#
# Vereisten:
#   - ~/recruitin/.env bestaat met ANTHROPIC_API_KEY + LEMLIST_API_KEY + SLACK_WEBHOOK_URL
#   - Fase 2 done: SUPABASE_URL + SUPABASE_KEY (service_role) capt'd uit nieuw V3 project
#   - Fase 3 done: LEMLIST_CAMPAIGN_ID = ID van JobDigger V3 P12 campagne
#
# Repo target: WouterArtsRecruitin/recruitin-jobdigger-v3

REPO="WouterArtsRecruitin/recruitin-jobdigger-v3"

# ───────── SECRETS (encrypted, alleen workflow leest) ─────────

# 1. ANTHROPIC_API_KEY — uit ~/recruitin/.env
gh secret set ANTHROPIC_API_KEY --repo "$REPO" --body "$(grep '^ANTHROPIC_API_KEY=' ~/recruitin/.env | cut -d= -f2-)"

# 2. LEMLIST_API_KEY — uit ~/recruitin/.env
gh secret set LEMLIST_API_KEY --repo "$REPO" --body "$(grep '^LEMLIST_API_KEY=' ~/recruitin/.env | cut -d= -f2-)"

# 3. LEMLIST_CAMPAIGN_ID — uit Fase 3 output (vervang VUL_IN)
gh secret set LEMLIST_CAMPAIGN_ID --repo "$REPO" --body "VUL_IN_NA_FASE_3"

# 4. SUPABASE_URL — uit Fase 2 (NIEUWE V3 project, niet de KT key in .env!)
#    Vorm: https://<ref>.supabase.co
gh secret set SUPABASE_URL --repo "$REPO" --body "VUL_IN_NA_FASE_2"

# 5. SUPABASE_KEY — service_role uit Fase 2 (NIEUWE V3 project)
gh secret set SUPABASE_KEY --repo "$REPO" --body "VUL_IN_NA_FASE_2"

# 6. SLACK_WEBHOOK_URL — uit ~/recruitin/.env (optioneel, voor failure-alerts)
gh secret set SLACK_WEBHOOK_URL --repo "$REPO" --body "$(grep '^SLACK_WEBHOOK_URL=' ~/recruitin/.env | cut -d= -f2-)"

# ───────── VARS (niet encrypted, public values) ─────────

gh variable set CLAUDE_MODEL --repo "$REPO" --body "claude-opus-4-7"
gh variable set SUPABASE_BUCKET --repo "$REPO" --body "jobdigger-pdfs"
gh variable set LEAD_BATCH_SIZE --repo "$REPO" --body "20"

# ───────── VERIFY (read-only, safe to autorun) ─────────

echo "=== Secrets (names only, values hidden) ==="
gh secret list --repo "$REPO"
echo
echo "=== Vars (values shown) ==="
gh variable list --repo "$REPO"
