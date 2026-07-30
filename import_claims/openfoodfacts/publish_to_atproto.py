"""Publish unpublished Open Food Facts claims to ATProto PDS.

Reads ATPROTO_HANDLE, ATPROTO_APP_PASSWORD, and optionally ATPROTO_PDS_URL
from .env. Queries the DB for OFF claims with no claimAddress, builds
com.linkedclaims.claim records, publishes them via the PDS createRecord
endpoint, and updates claimAddress with the returned at:// URI.

Usage:
    cd /opt/shared/repos/trust-claim-data-pipeline
    python import_claims/openfoodfacts/publish_to_atproto.py
"""

import datetime
import os
import sys
import time

import requests

# Ensure project root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from lib.db import get_db_cursor, update_claim_address

ATPROTO_PDS_URL = os.getenv("ATPROTO_PDS_URL", "https://bsky.social")
ATPROTO_HANDLE = os.getenv("ATPROTO_HANDLE")
ATPROTO_APP_PASSWORD = os.getenv("ATPROTO_APP_PASSWORD")

COLLECTION = "com.linkedclaims.claim"
PUBLISH_DELAY_SECONDS = 0.5  # rate-limit between publishes


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


def get_unpublished_off_claims():
    """Query OFF claims that have not been published (claimAddress IS NULL)."""
    claims = []
    with get_db_cursor() as cur:
        cur.execute(
            """SELECT id, subject, claim, object, statement, "effectiveDate",
                      "sourceURI", "howKnown", aspect, score, stars, amt, unit,
                      confidence, "issuerId", "issuerIdType"
               FROM "Claim"
               WHERE ("claimAddress" IS NULL OR "claimAddress" = '')
                 AND "sourceURI" LIKE 'https://world.openfoodfacts.org/%%'
               ORDER BY id"""
        )
        columns = [desc[0] for desc in cur.description]
        for row in cur.fetchall():
            claims.append(dict(zip(columns, row)))
    return claims


def map_claim_to_record(claim):
    """Map a DB claim dict to an ATProto com.linkedclaims.claim record.

    Mirrors the field structure used by the Ceramic publisher in
    claims_to_ceramic/pipe.py make_compose_json(), adapted for ATProto.
    """
    record = {
        "$type": COLLECTION,
        "claimType": claim["claim"],
        "subject": claim["subject"],
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

    # Source information
    if claim.get("sourceURI"):
        record["source"] = {
            "howKnown": claim.get("howKnown") or "WEB_DOCUMENT",
            "uri": claim["sourceURI"],
        }

    # Stars and aspect are top-level fields in the lexicon
    if claim.get("stars") is not None:
        record["stars"] = int(claim["stars"])

    if claim.get("aspect"):
        record["aspect"] = claim["aspect"]

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
    resp.raise_for_status()
    data = resp.json()
    return data["uri"]


def main():
    print("=== Open Food Facts ATProto Publisher ===")

    did, access_jwt = create_session()
    print(f"Authenticated as {did}")

    claims = get_unpublished_off_claims()
    print(f"Found {len(claims)} unpublished OFF claims")

    if not claims:
        print("Nothing to publish.")
        return

    published = 0
    errors = 0

    for claim in claims:
        try:
            record = map_claim_to_record(claim)
            at_uri = publish_record(did, access_jwt, record)
            update_claim_address(claim["id"], at_uri)
            published += 1
            print(f"  Published claim {claim['id']}: {at_uri}")
        except requests.HTTPError as e:
            errors += 1
            print(f"  Error publishing claim {claim['id']}: {e}")
            if e.response is not None and e.response.status_code == 401:
                print("  Session expired, re-authenticating...")
                try:
                    did, access_jwt = create_session()
                except Exception:
                    print("  Re-auth failed, stopping.")
                    break
        except Exception as e:
            errors += 1
            print(f"  Error publishing claim {claim['id']}: {e}")

        time.sleep(PUBLISH_DELAY_SECONDS)

    print(f"\n=== Summary ===")
    print(f"Total unpublished: {len(claims)}")
    print(f"Published: {published}")
    if errors:
        print(f"Errors: {errors}")


if __name__ == "__main__":
    main()
