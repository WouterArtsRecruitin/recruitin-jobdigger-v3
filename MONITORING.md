# JobDigger V3 — Monitoring & Runbook

**Status:** LIVE (go-live 2026-05-19)

## Daily Metrics

Check recent runs:
```bash
gh run list --workflow=daily-cron.yml --repo WouterArtsRecruitin/recruitin-jobdigger-v3 --limit 7
```

Expected:
- Runs every day at 07:00 UTC
- Duration: ~5-10 minutes
- Batch size: 20 leads/day (configurable via `LEAD_BATCH_SIZE` var)

## Costs

**Anthropic API:**
- Track usage: https://console.anthropic.com/account/usage
- Expected: €3–5/day @ 20 leads/day
- **Workspace usage cap: €15/day** (guardrail, prevents runaway cost)

**Supabase:**
- Storage: jobdigger-pdfs bucket (40 PDFs/day @ 500KB each = 20MB/day)
- Bandwidth: public PDFs in emails (metered)

## Slack Alerts

- **On failure:** `:rotating_light: JobDigger daily run FAILED — [run URL]`
- **On success:** `:white_check_mark: JobDigger V3 daily run OK — [run URL]`

## Troubleshooting

### Run failed

1. Check logs: `gh run view <run_id> --log`
2. Common causes:
   - Missing secret (check `gh secret list`)
   - API rate limit (Lemlist 429, Anthropic quota)
   - Supabase connection (RLS policy? storage key?)
   - Claude distill returned non-JSON

3. Fix & re-run:
   ```bash
   gh workflow run daily-cron.yml --repo WouterArtsRecruitin/recruitin-jobdigger-v3 -f lead_batch_size=2
   ```

### Lead not in Lemlist

1. Check lead passed ICP filter:
   - `grep "ICP qualified" logs/daily_run_*.log`
2. Check Supabase PDFs exist:
   - `supabase storage ls jobdigger-pdfs` (via CLI)
3. Check Lemlist API response:
   - Logs show lemlist result: `{"_id": "...", "status": "..."`

### Email not received

1. Check Lemlist campaign:
   - Visit https://app.lemlist.com/campaigns/cam_B3BDF7MeBCcTN3CtS/sequence
   - Verify 5 touches exist (days 0/2/5/9/14)
   - Check lead is in campaign: https://app.lemlist.com/campaigns/cam_B3BDF7MeBCcTN3CtS/contacts

2. Check reply detection:
   - Lemlist dashboard → campaign settings → "Reply detection" = ON
   - Webhook should update Pipedrive stage "Lead Warm"

### Canary Email Issues

If testing with `CANARY_EMAIL=warts@recruitin.nl`:

1. Set var temporarily:
   ```bash
   gh variable set CANARY_EMAIL --repo WouterArtsRecruitin/recruitin-jobdigger-v3 --body "warts@recruitin.nl"
   ```

2. Run test batch:
   ```bash
   gh workflow run daily-cron.yml --repo WouterArtsRecruitin/recruitin-jobdigger-v3 -f lead_batch_size=1
   ```

3. Verify email in inbox within 5 min
4. Unsubscribe test: click link, then verify in Lemlist unsubscribes list
5. Clear var after testing:
   ```bash
   gh variable delete CANARY_EMAIL --repo WouterArtsRecruitin/recruitin-jobdigger-v3
   ```

## GO LIVE Checklist (2026-05-19)

- [x] Fase 0: Diagnosed workflow failures (missing secrets)
- [x] Fase 1: Cloned repo locally
- [x] Fase 2: Created Supabase project + RLS
- [x] Fase 3: Created Lemlist V3 P12 campaign
- [x] Fase 4: Set GitHub secrets (6) + vars (3)
- [x] Fase 5: Local dry-run passed (2/2 leads)
- [x] Fase 6: Workflow dispatch test (batch=2) passed
- [x] Fase 7: Canary test (batch=1) in progress
- [ ] Fase 8: GO LIVE (batch=20, monitoring active)

## Post-GO LIVE (First 72 Hours)

| Time | Task | Owner |
|------|------|-------|
| T+2h | First cron run should complete (check Slack) | Auto |
| T+24h | Check 20 leads in Lemlist V3 P12 | Manual |
| T+24h | Verify PDFs in Supabase bucket | Manual |
| T+48h | Monitor for first reply in Pipedrive | Manual |
| T+72h | Cost check (should be <€5) | Manual |

## Incident Response

If pipeline breaks:

```bash
# Disable cron immediately
gh workflow disable daily-cron.yml --repo WouterArtsRecruitin/recruitin-jobdigger-v3

# Pause campaign in Lemlist
# Visit: https://app.lemlist.com/campaigns/cam_B3BDF7MeBCcTN3CtS → pause

# Debug logs
gh run list --repo WouterArtsRecruitin/recruitin-jobdigger-v3 --limit 1 | awk '{print $1}' | xargs -I {} gh run view {} --log --repo WouterArtsRecruitin/recruitin-jobdigger-v3

# Re-enable after fix
gh workflow enable daily-cron.yml --repo WouterArtsRecruitin/recruitin-jobdigger-v3
```

## References

- **Campaign:** https://app.lemlist.com/campaigns/cam_B3BDF7MeBCcTN3CtS/sequence
- **Supabase:** https://supabase.com/dashboard/project/iymhfiwxjzbmicteacet
- **Lemlist API:** https://api.lemlist.com (docs in memory)
- **Scripts:** `scripts/daily_automation.py` (core pipeline)
- **Cron:** `.github/workflows/daily-cron.yml` (07:00 UTC daily)
