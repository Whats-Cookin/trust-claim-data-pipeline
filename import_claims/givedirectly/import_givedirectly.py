#!/usr/bin/env python3
"""Import GiveDirectly's headline impact claim into LinkedClaims.

GiveDirectly publishes a clear, third-party-auditable figure: cash delivered and
people reached. That is the program's headline claim. Recipient-level accounts
(GDLive) are a separate, harder source — GDLive is a client-rendered app with no
open feed — and the stronger path for those is independent verification by RTV
volunteers (signed, FIRST_HAND), not scraping.

We always link to the source (givedirectly.org/financials). An Image row is added
(the site's social image) so the claim is visual. Idempotent on subject+claim.
"""
import datetime
import os
import re
import urllib.request

import psycopg2
from dotenv import dotenv_values

UA = "linkedtrust-data-pipeline/0.1"
ENV = dotenv_values(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

SUBJECT = "https://www.givedirectly.org"
SOURCE = "https://www.givedirectly.org/financials/"

CLAIM = {
    "subject": SUBJECT,
    "claim": "impact",
    "statement": ("GiveDirectly has delivered ~$900M in cash directly to ~1.7M "
                  "people living in poverty (cumulative, through 2025)."),
    "aspect": "impact:cash transfers, poverty",
    "amt": 900000000, "unit": "USD",
    "howMeasured": "recipients reached: ~1,700,000 (GiveDirectly financials)",
    "sourceURI": SOURCE,
    "howKnown": "WEB_DOCUMENT",
    "author": "GiveDirectly",
    "effectiveDate": datetime.date(2025, 1, 1),
    "confidence": 0.8,
    "issuerIdType": "URL",
}
COLS = ("subject", "claim", "statement", "aspect", "amt", "unit", "howMeasured",
        "sourceURI", "howKnown", "author", "effectiveDate", "confidence",
        "issuerId", "issuerIdType")


def fetch_og_image(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html)
        return m.group(1) if m else None
    except Exception:
        return None


def _cfg(key, default=None):
    return os.environ.get(key) or ENV.get(key, default)


def connect():
    url = _cfg("DATABASE_URL")
    if url:
        return psycopg2.connect(url)
    return psycopg2.connect(
        host=_cfg("DB_HOST"), dbname=_cfg("DB_NAME"), user=_cfg("DB_USER"),
        password=_cfg("DB_PASSWORD"), port=_cfg("DB_PORT", "5432"))


def main():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""SELECT id FROM "User" WHERE name='SPIDER' LIMIT 1""")
    row = cur.fetchone()
    if not row:
        cur.execute("""INSERT INTO "User"(name, email, "authType")
                       VALUES('SPIDER', 'spider@linkedtrust.us', 'PASSWORD') RETURNING id""")
        row = cur.fetchone()
    issuer = f"http://trustclaims.whatscookin.us/users/{row[0]}"

    cur.execute("""SELECT id FROM "Claim" WHERE subject=%s AND claim=%s""",
                (SUBJECT, CLAIM["claim"]))
    existing = cur.fetchone()
    if existing:
        print(f"already imported: claim {existing[0]}")
        conn.close()
        return

    vals = dict(CLAIM, issuerId=issuer)
    cur.execute(
        f'INSERT INTO "Claim" ({", ".join(chr(34)+c+chr(34) for c in COLS)}) '
        f'VALUES ({", ".join(["%s"]*len(COLS))}) RETURNING id',
        tuple(vals[c] for c in COLS))
    cid = cur.fetchone()[0]

    img = fetch_og_image("https://www.givedirectly.org/") or fetch_og_image(SOURCE)
    if img:
        cur.execute(
            'INSERT INTO "Image" ("claimId", url, "effectiveDate", owner, signature) '
            'VALUES (%s, %s, %s, %s, %s)',
            (cid, img, CLAIM["effectiveDate"], issuer, ""))
    conn.commit()
    conn.close()
    print(f"imported GiveDirectly headline claim {cid} (image: {'yes' if img else 'no'})")


if __name__ == "__main__":
    main()
