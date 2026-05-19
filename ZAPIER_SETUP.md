# Zapier Setup — JobDigger Email → Supabase

Goal: Automatically pick up JobDigger's daily email to `wouter.arts@recruitin.nl`, extract the Excel attachment, and upload it to Supabase so the V3 cron picks it up at 07:00 UTC.

## Architecture

```
JobDigger (sender)
   ↓ daily email + .xlsx attachment
wouter.arts@recruitin.nl (Microsoft 365)
   ↓ Zapier Outlook trigger
Zapier Zap
   ↓ extract attachment
Supabase Storage bucket `jobdigger-input` (private)
   ↓ scripts/fetch_jobdigger_input.py
GitHub Actions workflow (07:00 UTC)
   ↓ data/daily_vacancies.xlsx
JobDigger V3 pipeline
```

## Required values

- **Supabase URL:** `https://iymhfiwxjzbmicteacet.supabase.co`
- **Supabase bucket:** `jobdigger-input` (already created, private)
- **Supabase service_role key:** in `~/recruitin/.env` as `SUPABASE_KEY` (V3 project key)
- **Target object path:** `daily_vacancies_{YYYYMMDD}.xlsx` (timestamped, latest wins)

## Step-by-step Zap config

### 1. Create new Zap

Name: `JobDigger Daily Email → Supabase`

### 2. Trigger: Microsoft Outlook — New Email

- **App:** Microsoft Outlook
- **Event:** New Email
- **Account:** `wouter.arts@recruitin.nl`
- **Folder:** Inbox (or sub-folder if you filter JobDigger emails there)

### 3. Filter step: Only match JobDigger emails

Add a Zapier "Filter" step that only continues if:
- **Sender Email** (exact) → `noreply@jobdigger.nl`
- AND **Has Attachments** → `true`

### 4. Action: Files by Zapier — Read Attachment

- **App:** Files by Zapier (or use the attachment URL from Outlook directly)
- **Event:** None needed — most Outlook triggers expose the first attachment as `Attachment 1 Url`

### 5. Action: Supabase — Upload File (via REST API)

Zapier does not have a native Supabase action, so use **Webhooks by Zapier**:

- **App:** Webhooks by Zapier
- **Event:** Custom Request
- **Method:** `POST`
- **URL:** `https://iymhfiwxjzbmicteacet.supabase.co/storage/v1/object/jobdigger-input/daily_vacancies_{{zap_meta_human_now_iso}}.xlsx`
  (or simpler: `.../daily_vacancies_latest.xlsx` — overwrites each day)
- **Data Pass-Through?** No
- **Data:** Body = `Attachment 1 Url` content (Zapier streams the file)
- **Headers:**
  ```
  Authorization: Bearer <SUPABASE_SERVICE_ROLE_KEY>
  Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  x-upsert: true
  ```

The `x-upsert: true` header allows overwriting yesterday's file when using a static filename.

### 6. Test the Zap

- Trigger manually using a recent JobDigger email in your inbox
- Verify the file appears in Supabase Storage → `jobdigger-input` bucket
- Run the GitHub workflow manually with `lead_batch_size=1` to confirm it picks up the file

### 7. Turn on the Zap

Once test passes, toggle Zap to **ON**. It will fire automatically each morning when the JobDigger email arrives.

## Troubleshooting

### Excel not appearing in Supabase
- Check Zap history for errors (Zapier dashboard)
- Verify the service_role key has not expired
- Check `x-upsert: true` header (without it, second upload to same name will fail)

### GitHub workflow doesn't see new file
- The workflow downloads the **most-recently-updated** file in the bucket
- If using timestamped filenames, this is automatic
- If using `daily_vacancies_latest.xlsx`, ensure `x-upsert: true` is set so it overwrites

### Workflow runs before email arrives
- Cron fires at **07:00 UTC** = 08:00 CET (winter) / 09:00 CEST (summer)
- JobDigger must send the email before 07:00 UTC
- If JobDigger sends later, change cron in `.github/workflows/daily-cron.yml`:
  ```yaml
  - cron: "0 9 * * *"  # 09:00 UTC = 10:00 CET
  ```

## Manual fallback

If Zapier breaks, you can manually upload the Excel:

```bash
cd ~/projects/recruitin-jobdigger-v3
.venv/bin/python3.13 -c "
from supabase import create_client
import os
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
with open('/path/to/jobdigger.xlsx', 'rb') as f:
    client.storage.from_('jobdigger-input').upload(
        'daily_vacancies_manual.xlsx', f,
        {'content-type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'upsert': 'true'}
    )
print('Uploaded')
"
```
