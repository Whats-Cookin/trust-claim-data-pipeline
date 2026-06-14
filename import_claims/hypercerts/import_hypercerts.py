#!/usr/bin/env python3
"""Import hypercerts (impact claims) from the live Hypercerts GraphQL API.

Each real hypercert -> one LinkedClaim (claim='impact', self-asserted by the
minter, howKnown=WEB_DOCUMENT) plus an Image row so the claim is visual.

We always link to the source: subject + sourceURI are the web-loadable hypercert
page (https://app.hypercerts.org/hypercerts/<id>), the canonical IPFS metadata
CID is kept in digestMultibase, and the project's own site is stored as object.

DB target + creds come from the repo .env (DB_HOST/DB_NAME/DB_USER/...). Run:
    python3 import_hypercerts.py [N]      # N = how many real ones to import (default 40)
Idempotent: skips hypercerts already imported (same subject + claim='impact').
"""
import datetime
import json
import os
import re
import sys
import urllib.request

import psycopg2
from dotenv import dotenv_values

API = "https://api.hypercerts.org/v1/graphql"
HC_PAGE = "https://app.hypercerts.org/hypercerts/{}"
SCAN = 250                       # how many to pull before filtering to the real ones
UA = "linkedtrust-data-pipeline/0.1"

ENV = dotenv_values(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Names/descriptions that mark test/junk entries we must not import.
JUNK_RE = re.compile(r"(?i)\b(test|testing|lorem ipsum|showdown|realize it)\b")


def gql(query):
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def _cfg(key, default=None):
    # env var wins over .env, so prod can override without editing files
    return os.environ.get(key) or ENV.get(key, default)


def db():
    url = _cfg("DATABASE_URL")
    if url:
        return psycopg2.connect(url)
    return psycopg2.connect(
        host=_cfg("DB_HOST"), dbname=_cfg("DB_NAME"), user=_cfg("DB_USER"),
        password=_cfg("DB_PASSWORD"), port=_cfg("DB_PORT", "5432"))


def spider_issuer(cur):
    """Return the SPIDER issuer URI, creating the SPIDER user if absent.

    Never silently fall back to user 1 — on prod that is a real person.
    """
    cur.execute("""SELECT id FROM "User" WHERE name='SPIDER' LIMIT 1""")
    row = cur.fetchone()
    if not row:
        cur.execute("""INSERT INTO "User"(name, email, "authType")
                       VALUES('SPIDER', 'spider@linkedtrust.us', 'PASSWORD')
                       RETURNING id""")
        row = cur.fetchone()
    return f"http://trustclaims.whatscookin.us/users/{row[0]}"


def norm_name(name):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (name or "").lower())).strip()


def clean(text):
    text = re.sub(r"[*#>_`]", "", text or "")        # strip markdown
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_real(m):
    name = (m.get("name") or "").strip()
    desc = (m.get("description") or "").strip()
    scope = [s for s in (m.get("work_scope") or []) if not s.startswith("⭔")]
    if not name or JUNK_RE.search(name):
        return False
    if len(desc) < 60 or desc.lower().startswith("this is a hypercert"):
        return False
    if "lorem ipsum" in desc.lower():
        return False
    return bool(scope)


def to_date(ts):
    if not ts:
        return None
    return datetime.datetime.fromtimestamp(int(ts), datetime.UTC).date()


def map_claim(h, issuer):
    m = h["metadata"]
    hid = h["hypercert_id"]
    page = HC_PAGE.format(hid)
    scope = [s for s in (m.get("work_scope") or []) if not s.startswith("⭔")]
    name, desc = m["name"].strip(), clean(m.get("description"))
    statement = f"{name} — {desc}"
    if len(statement) > 300:
        statement = statement[:297] + "…"
    return {
        "subject": page,
        "claim": "impact",
        "statement": statement,
        "object": (m.get("external_url") or "") or None,
        "aspect": "impact:" + ", ".join(scope) if scope else None,
        "sourceURI": page,                       # web-loadable source
        "howKnown": "WEB_DOCUMENT",
        "effectiveDate": to_date(m.get("work_timeframe_from")),
        "digestMultibase": h.get("uri"),         # canonical IPFS metadata CID
        "author": "Hypercert minter (self-asserted)",
        "confidence": 0.5,
        "issuerId": issuer,
        "issuerIdType": "URL",
    }


CLAIM_COLS = ("subject", "claim", "statement", "object", "aspect", "sourceURI",
              "howKnown", "effectiveDate", "digestMultibase", "author",
              "confidence", "issuerId", "issuerIdType")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40

    # Pass 1: pull candidates (no image -> light payload), filter to the real ones.
    data = gql('{ hypercerts(first: %d, sort: {by: {attestations_count: descending}}) '
               '{ data { hypercert_id uri metadata { name description external_url '
               'work_scope work_timeframe_from } } } }' % SCAN)
    cands = [h for h in data["hypercerts"]["data"] if h.get("metadata") and is_real(h["metadata"])]
    print(f"scanned {SCAN}, real candidates: {len(cands)}")

    conn = db()
    conn.autocommit = False
    cur = conn.cursor()
    issuer = spider_issuer(cur)

    cur.execute("""SELECT subject FROM "Claim" WHERE claim='impact'
                   AND subject LIKE 'https://app.hypercerts.org/%'""")
    seen = {r[0] for r in cur.fetchall()}
    seen_names = set()   # project-level dedupe (same project minted more than once)

    insert_claim = (f'INSERT INTO "Claim" ({", ".join(chr(34)+c+chr(34) for c in CLAIM_COLS)}) '
                    f'VALUES ({", ".join(["%s"] * len(CLAIM_COLS))}) RETURNING id')
    insert_image = ('INSERT INTO "Image" ("claimId", url, "effectiveDate", owner, signature) '
                    'VALUES (%s, %s, %s, %s, %s)')

    imported = []
    for h in cands:
        if len(imported) >= n:
            break
        rec = map_claim(h, issuer)
        nm = norm_name(h["metadata"].get("name"))
        if rec["subject"] in seen or nm in seen_names:
            continue
        seen_names.add(nm)
        cur.execute(insert_claim, tuple(rec[c] for c in CLAIM_COLS))
        cid = cur.fetchone()[0]
        # Pass 2: fetch this one's image (data: URI) and attach it.
        try:
            img = gql('{ hypercerts(first: 1, where: {hypercert_id: {eq: "%s"}}) '
                      '{ data { metadata { image } } } }' % h["hypercert_id"])
            url = (img["hypercerts"]["data"][0]["metadata"] or {}).get("image")
        except Exception:
            url = None
        if url:
            eff = rec["effectiveDate"] or datetime.date.today()
            cur.execute(insert_image, (cid, url, eff, issuer, ""))
        imported.append((cid, h["metadata"]["name"], rec["subject"]))
        seen.add(rec["subject"])

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nimported {len(imported)} hypercert claims:")
    for cid, name, sub in imported:
        print(f"  claim {cid}: {name[:55]}")
    print("\nfirst subject:", imported[0][2] if imported else "(none)")


if __name__ == "__main__":
    main()
