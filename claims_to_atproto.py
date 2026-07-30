"""Publish unpublished claims to ATProto PDS.

Reads ATPROTO_HANDLE, ATPROTO_APP_PASSWORD, and ATPROTO_PDS_URL
from .env. Queries the DB for claims with no claimAddress, builds
com.linkedclaims.claim records, publishes them via the PDS createRecord
endpoint, and updates claimAddress with the returned at:// URI.

Usage:
    cd /opt/shared/repos/trust-claim-data-pipeline
    python -m claims_to_atproto.publish_unpublished
"""

import datetime
import os
import sys
import time

import requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from lib.db import get_db_cursor, update_claim_address

ATPROTO_PDS_URL = os.getenv("ATPROTO_PDS_URL", "https://bsky.social")
ATPROTO_HANDLE = os.getenv("ATPROTO_HANDLE")
ATPROTO_APP_PASSWORD = os.getenv("ATPROTO_APP_PASSWORD")
BASE_URL = os.getenv("BASE_URL", "https://live.linkedtrust.us")

COLLECTION = "com.linkedclaims.claim"
PUBLISH_DELAY_SECONDS = 1.0


def unpublished_claims_generator():
    """Yield unpublished claims that come from known spider sources.

    Currently scoped to OpenFoodFacts claims. Add more sourceURI prefixes
    as additional spiders are integrated.
    """
    known_sources = [
        "https://world.openfoodfacts.org/",
    ]
    source_filter = " OR ".join(['"sourceURI" LIKE \'%s%%\'' % s for s in known_sources])
    query = f'''
        SELECT id, subject, claim, object, statement, "effectiveDate",
               "sourceURI", "howKnown", "dateObserved", "digestMultibase",
               author, curator, aspect, score, stars, amt, unit,
               "howMeasured", "intendedAudience", "respondAt",
               confidence, "issuerId", "issuerIdType", "claimAddress", proof
        FROM "Claim"
        WHERE ("claimAddress" IS NULL OR "claimAddress" = '')
          AND ({source_filter})
    '''
    with get_db_cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        while True:
            rows = cur.fetchmany(1000)
            if not rows:
                break
            for row in rows:
                yield dict(zip(columns, row))


def create_session():
    """Authenticate with the PDS and return (did, access_jwt)."""
    if not ATPROTO_HANDLE or not ATPROTO_APP_PASSWORD:
        print("Error: ATPROTO_HANDLE and ATPROTO_APP_PASSWORD must be set in .env")
        sys.exit(1)

    resp = requests.post(
        f"{ATPROTO_PDS_URL}/xrpc/com.atproto.server.createSession",
        json={"identifier": ATPROTO_HANDLE, "password": ATPROTO_APP_PASSWORD},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["did"], data["accessJwt"]


def map_claim_to_record(claim):
    """Map a DB claim dict to an ATProto com.linkedclaims.claim record.

    Matches the field structure used by trust_claim_backend/src/services/atprotoPublisher.ts.
    """
    claim_id = claim.get("id")
    record = {
        "$type": COLLECTION,
        "claimUri": claim.get("claimAddress") or (f"{BASE_URL}/api/claim/{claim_id}" if claim_id else None),
        "subject": claim["subject"],
        "claimType": claim["claim"],
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    if claim.get("statement"):
        record["statement"] = claim["statement"]

    if claim.get("object"):
        record["object"] = claim["object"]

    effective = claim.get("effectiveDate")
    if effective:
        if isinstance(effective, (datetime.date, datetime.datetime)):
            record["effectiveDate"] = effective.isoformat()
        else:
            record["effectiveDate"] = str(effective)

    if claim.get("confidence") is not None:
        record["confidence"] = str(claim["confidence"])

    # Full source object — matches backend atprotoPublisher.ts
    source = {}
    if claim.get("sourceURI"):
        source["uri"] = claim["sourceURI"]
    if claim.get("howKnown"):
        source["howKnown"] = claim["howKnown"]
    if claim.get("author"):
        source["author"] = claim["author"]
    if claim.get("curator"):
        source["curator"] = claim["curator"]
    if claim.get("dateObserved"):
        source["dateObserved"] = str(claim["dateObserved"])
    if claim.get("digestMultibase"):
        source["digestMultibase"] = claim["digestMultibase"]
    if source:
        record["source"] = source

    if claim.get("stars") is not None:
        record["stars"] = int(claim["stars"])

    if claim.get("aspect"):
        record["aspect"] = claim["aspect"]

    if claim_id:
        record["respondAt"] = f"{BASE_URL}/api/claim/{claim_id}/validate"

    return record


def publish_record(did, access_jwt, record):
    """Publish a single record to ATProto PDS. Returns the at:// URI."""
    resp = requests.post(
        f"{ATPROTO_PDS_URL}/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {access_jwt}"},
        json={
            "repo": did,
            "collection": COLLECTION,
            "record": record,
        },
        timeout=30,
    )
    if not resp.ok:
        print(f"  PDS response: {resp.status_code} {resp.text[:500]}")
        print(f"  Record keys: {list(record.keys())}")
    resp.raise_for_status()
    data = resp.json()
    return data["uri"]


def is_useful(claim):
    """Return True if the claim has enough fields to publish."""
    return bool(
        claim.get("claim")
        and claim.get("subject")
        and (claim.get("statement") or claim.get("object"))
        and claim.get("effectiveDate")
    )


def publish_unpublished():
    """Publish all unpublished claims to ATProto PDS."""
    did, access_jwt = create_session()
    print(f"Authenticated as {did}")

    total = 0
    published = 0
    skipped = 0
    errors = 0

    for claim in unpublished_claims_generator():
        if not is_useful(claim):
            skipped += 1
            print(f"  Skipping claim {claim['id']} ({claim.get('subject', '?')[:40]}) - missing fields")
            continue

        total += 1
        try:
            record = map_claim_to_record(claim)
            at_uri = publish_record(did, access_jwt, record)
            update_claim_address(claim["id"], at_uri)
            published += 1
            print(f"  Published claim {claim['id']}: {at_uri}")
        except requests.HTTPError as e:
            errors += 1
            print(f"  Error publishing claim {claim['id']}: {e}")
            if e.response is not None:
                print(f"  PDS error: {e.response.status_code} - {e.response.text[:300]}")
            if e.response is not None and e.response.status_code == 401:
                print("  Session expired, re-authenticating...")
                try:
                    did, access_jwt = create_session()
                except Exception:
                    print("  Re-auth failed, stopping.")
                    break
            if e.response is not None and e.response.status_code == 429:
                print("  Rate limited, backing off for 30s...")
                time.sleep(30)
                continue
        except Exception as e:
            errors += 1
            print(f"  Error publishing claim {claim['id']}: {e}")

        time.sleep(PUBLISH_DELAY_SECONDS)

    print(f"\n=== Summary ===")
    print(f"Total in batch: {total}")
    print(f"Published: {published}")
    print(f"Skipped (missing fields): {skipped}")
    if errors:
        print(f"Errors: {errors}")


if __name__ == "__main__":
    publish_unpublished()