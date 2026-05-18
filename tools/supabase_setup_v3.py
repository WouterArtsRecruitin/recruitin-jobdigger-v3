"""JobDigger V3 — Supabase project setup.

After the project is provisioned (via `supabase projects create` or dashboard),
this script:
  1. Creates the `jobdigger-pdfs` storage bucket (public read)
  2. Applies RLS policies (anyone reads, service_role writes)
  3. Smoke-tests by uploading a 1-page PDF and fetching it via public URL
  4. Cleans up the smoke test

Usage:
    SUPABASE_URL=https://<ref>.supabase.co \
    SUPABASE_KEY=<service_role_key> \
    python tools/supabase_setup_v3.py

Requirements: supabase-py (already in requirements.txt).
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import requests
from supabase import Client, create_client

BUCKET = "jobdigger-pdfs"


def env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        sys.exit(f"Missing required env var: {key}")
    return val


def ensure_bucket(client: Client) -> None:
    existing = {b.name for b in client.storage.list_buckets()}
    if BUCKET in existing:
        print(f"  bucket '{BUCKET}' already exists")
        return
    client.storage.create_bucket(BUCKET, options={"public": True})
    print(f"  bucket '{BUCKET}' created (public read)")


def apply_rls(supabase_url: str, service_key: str) -> None:
    """Apply storage RLS via the Postgres REST endpoint.

    Public buckets already allow anon read by default; we still want
    explicit policies so the intent is documented in the DB.
    """
    sql = """
    -- Drop existing JobDigger-specific policies (idempotent)
    drop policy if exists "jd_anon_read" on storage.objects;
    drop policy if exists "jd_service_insert" on storage.objects;
    drop policy if exists "jd_service_update" on storage.objects;
    drop policy if exists "jd_service_delete" on storage.objects;

    -- Anyone can read PDFs (public bucket pattern)
    create policy "jd_anon_read" on storage.objects
        for select using (bucket_id = 'jobdigger-pdfs');

    -- Only service_role can write/modify/delete
    create policy "jd_service_insert" on storage.objects
        for insert with check (
            bucket_id = 'jobdigger-pdfs' and auth.role() = 'service_role'
        );
    create policy "jd_service_update" on storage.objects
        for update using (
            bucket_id = 'jobdigger-pdfs' and auth.role() = 'service_role'
        );
    create policy "jd_service_delete" on storage.objects
        for delete using (
            bucket_id = 'jobdigger-pdfs' and auth.role() = 'service_role'
        );
    """

    resp = requests.post(
        f"{supabase_url}/rest/v1/rpc/exec_sql",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        },
        json={"sql": sql},
        timeout=30,
    )
    if resp.status_code == 404:
        # exec_sql RPC niet aanwezig op nieuwe projecten — gebruiker moet
        # policies handmatig via dashboard zetten. Public-read werkt sowieso
        # default voor public buckets.
        print("  ! exec_sql RPC not available — applying RLS via SQL editor")
        print("    Run dit handmatig in dashboard SQL editor:")
        print("    " + sql.replace("\n", "\n    "))
        return
    resp.raise_for_status()
    print("  RLS policies applied")


def smoke_test(client: Client, supabase_url: str) -> None:
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
        b"0000000052 00000 n\n0000000099 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF\n"
    )
    key = "_smoketest/test.pdf"

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        path = f.name

    try:
        client.storage.from_(BUCKET).upload(
            key, path, file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        public_url = client.storage.from_(BUCKET).get_public_url(key)
        print(f"  uploaded → {public_url}")

        resp = requests.get(public_url, timeout=10)
        resp.raise_for_status()
        assert resp.content.startswith(b"%PDF"), "Public fetch did not return PDF bytes"
        print(f"  fetched {len(resp.content)} bytes ✓")
    finally:
        client.storage.from_(BUCKET).remove([key])
        Path(path).unlink(missing_ok=True)
        print("  cleaned up smoke-test PDF")


def main() -> int:
    supabase_url = env("SUPABASE_URL")
    service_key = env("SUPABASE_KEY")

    print(f"Connecting to {supabase_url}")
    client = create_client(supabase_url, service_key)

    print("[1/3] Ensuring bucket")
    ensure_bucket(client)

    print("[2/3] Applying RLS policies")
    apply_rls(supabase_url, service_key)

    print("[3/3] Smoke test (upload → fetch → delete)")
    smoke_test(client, supabase_url)

    print("\n✓ Supabase JobDigger V3 setup complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
