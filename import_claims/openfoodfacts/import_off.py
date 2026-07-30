"""Import Open Food Facts certifications and ratings as LinkedTrust claims.

Fetches products from the OFF API, generates one claim per certification/rating
per product, deduplicates against existing claims, and batch-inserts into the
Claim table.

Usage:
    cd /opt/shared/repos/trust-claim-data-pipeline
    python import_claims/openfoodfacts/import_off.py
"""

import json
import os
import sys
import datetime
import time

import requests

# Ensure project root and script dir are on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from lib.db import get_db_cursor, insert_data
from label_mappings import CERTIFICATION_MAPPINGS, RATING_MAPPINGS


def load_config():
    config_path = os.path.join(SCRIPT_DIR, "config.json")
    with open(config_path) as f:
        return json.load(f)


def get_spider_output_file():
    """Find the most recent spider output file, if any."""
    spider_data_dir = os.path.abspath(
        os.path.join(SCRIPT_DIR, "..", "..", "spider_claims", "openfoodfacts", "data")
    )
    if not os.path.isdir(spider_data_dir):
        return None
    files = [
        f for f in os.listdir(spider_data_dir) if f.startswith("off_products_") and f.endswith(".json")
    ]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(os.path.join(spider_data_dir, f)))
    return os.path.join(spider_data_dir, files[-1])


def load_products_from_spider():
    """Load products from the spider's output file."""
    output_file = get_spider_output_file()
    if not output_file:
        return None
    print(f"Loading products from spider output: {output_file}")
    with open(output_file) as f:
        data = json.load(f)
    products = data.get("products", [])
    print(f"Loaded {len(products)} products from {output_file}")
    return products


def get_spider_id():
    """Look up the SPIDER user ID, falling back to 1."""
    with get_db_cursor() as cur:
        cur.execute("""SELECT id FROM "User" WHERE name='SPIDER'""")
        row = cur.fetchone()
        return row[0] if row else 1


def get_existing_off_claims():
    """Load existing OFF claims for dedup. Returns set of (subject, object, claim) tuples."""
    existing = set()
    with get_db_cursor() as cur:
        cur.execute(
            """SELECT subject, object, claim FROM "Claim"
               WHERE "sourceURI" LIKE 'https://world.openfoodfacts.org/product/%%'"""
        )
        for row in cur.fetchall():
            existing.add((row[0], row[1], row[2]))
    return existing


def fetch_page_with_retry(url, params, headers, max_retries=3):
    """Fetch a single API page with retry on transient errors (429, 5xx)."""
    for attempt in range(max_retries):
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        if resp.status_code in (429, 500, 502, 503, 504):
            wait = (attempt + 1) * 10
            print(f"  HTTP {resp.status_code}, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()  # raise the last error


def fetch_products_via_search(config):
    """Fetch products via the OFF search API with pagination and rate limiting.

    If config["search_per_label"] is true, searches each label individually
    to get more diverse results (the combined query only returns products
    with ALL labels).
    """
    products = []
    seen_codes = set()
    base_url = config["api_base_url"] + config["search_endpoint"]
    headers = {"User-Agent": config["user_agent"]}

    if config.get("search_per_label"):
        labels_to_search = [[label] for label in config["target_labels"]]
    else:
        labels_to_search = [config["target_labels"]]

    for labels in labels_to_search:
        label_tag = ",".join(labels)
        for page in range(1, config["max_pages"] + 1):
            params = {
                "labels_tags": label_tag,
                "fields": config["fields"],
                "page_size": config["page_size"],
                "page": page,
                "json": 1,
            }

            print(f"Fetching {label_tag} page {page}/{config['max_pages']}...")
            try:
                data = fetch_page_with_retry(base_url, params, headers)
            except requests.HTTPError as e:
                print(f"  Search failed for {label_tag} page {page}: {e}, moving on...")
                break

            page_products = data.get("products", [])
            if not page_products:
                print("  No more products, next label.")
                break

            new_on_page = 0
            for p in page_products:
                code = p.get("code")
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    products.append(p)
                    new_on_page += 1

            print(f"  Got {new_on_page} new products (total unique: {len(products)})")

            print(f"  Rate limiting: sleeping {config['rate_limit_seconds']}s...")
            time.sleep(config["rate_limit_seconds"])

    return products


def fetch_products_by_barcode(config):
    """Fallback: fetch individual products by barcode when search API is down.

    Uses the per-label facet pages to discover barcodes, then fetches each product.
    """
    headers = {"User-Agent": config["user_agent"]}
    fields = config["fields"]
    seen_codes = set()
    products = []
    limit = config["page_size"] * config["max_pages"]

    for label in config["target_labels"]:
        if len(products) >= limit:
            break
        # Facet URL: e.g. https://world.openfoodfacts.org/label/en:organic.json
        facet_url = f"{config['api_base_url']}/label/{label}.json"
        print(f"Fetching facet for {label}...")
        try:
            data = fetch_page_with_retry(
                facet_url, {"page_size": limit, "fields": fields}, headers
            )
        except Exception as e:
            print(f"  Facet failed for {label}: {e}, trying per-product fallback...")
            continue

        for p in data.get("products", []):
            code = p.get("code")
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)
            products.append(p)
            if len(products) >= limit:
                break

        time.sleep(config["rate_limit_seconds"])

    if not products:
        # Last resort: fetch a curated set of known certified barcodes
        print("Facets also unavailable. Fetching known certified product barcodes...")
        known_barcodes = [
            "03341148", "7613312317686", "4099200057699", "3256220110105",
            "3017620422003", "3175681851856", "8076809513388", "3263859883942",
            "3270190127529", "5449000000996", "8718215840428", "3270190022732",
            "5000112546415", "4056489641117", "3560070472475", "3564700014592",
            "8722700479451", "3228020200058", "3229820019307", "8000500310427",
        ]
        for barcode in known_barcodes:
            if len(products) >= limit:
                break
            url = f"{config['api_base_url']}/api/v2/product/{barcode}.json"
            try:
                resp = requests.get(
                    url, params={"fields": fields}, headers=headers, timeout=30
                )
                if resp.ok:
                    data = resp.json()
                    product = data.get("product")
                    if product and product.get("code"):
                        products.append(product)
                        print(f"  Fetched {barcode}: {product.get('product_name', '?')[:40]}")
            except Exception as e:
                print(f"  Error fetching {barcode}: {e}")
            time.sleep(1)

    return products


def fetch_products(config):
    """Fetch products, trying spider output first then falling back to direct API."""
    products = load_products_from_spider()
    if products:
        return products

    print("No spider output found, fetching directly from OFF API...")
    try:
        products = fetch_products_via_search(config)
        if products:
            return products
    except requests.HTTPError as e:
        print(f"Search API unavailable ({e}), falling back to individual product lookups...")

    return fetch_products_by_barcode(config)


def generate_claims(products, config, spider_id):
    """Generate claim dicts from OFF products.

    Returns a list of dicts, each with keys matching Claim table columns.
    """
    claims = []
    today = datetime.date.today().isoformat()
    issuer_id = f"http://trustclaims.whatscookin.us/users/{spider_id}"

    for product in products:
        barcode = product.get("code")
        name = product.get("product_name") or "Unknown product"
        brand = product.get("brands") or "Unknown brand"
        product_url = product.get("url") or f"https://world.openfoodfacts.org/product/{barcode}"
        object_url = f"https://world.openfoodfacts.org/product/{barcode}"

        # Certification claims from labels_tags
        labels = product.get("labels_tags") or []
        for tag in labels:
            mapping = CERTIFICATION_MAPPINGS.get(tag)
            if not mapping:
                continue

            claims.append({
                "subject": mapping["subject"],
                "object": object_url,
                "claim": "certified",
                "statement": f"{mapping['name']} certification for {name} by {brand}",
                "sourceURI": product_url,
                "howKnown": config["howknown"],
                "aspect": mapping["aspect"],
                "confidence": config["confidence"],
                "effectiveDate": today,
                "issuerId": issuer_id,
                "issuerIdType": "URL",
            })

        # Rating claims from score fields
        for field, mapping in RATING_MAPPINGS.items():
            value = product.get(field)
            if not value:
                continue

            # Normalize: nutriscore/ecoscore are letter grades, nova_group is int
            if field == "nova_group":
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    continue
                display_value = f"Group {value}"
            else:
                value = str(value).lower().strip()
                if value not in mapping["stars"]:
                    continue
                display_value = value.upper()

            stars = mapping["stars"].get(value)
            if stars is None:
                continue

            claims.append({
                "subject": mapping["subject"],
                "object": object_url,
                "claim": "rated",
                "statement": f"{mapping['name']} {display_value} for {name} by {brand}",
                "sourceURI": product_url,
                "howKnown": config["howknown"],
                "aspect": mapping["aspect"],
                "stars": stars,
                "confidence": config["confidence"],
                "effectiveDate": today,
                "issuerId": issuer_id,
                "issuerIdType": "URL",
            })

    return claims


def main():
    print("=== Open Food Facts Claim Importer ===")

    config = load_config()
    print(f"Confidence: {config['confidence']}, howKnown: {config['howknown']}")

    spider_id = get_spider_id()
    print(f"SPIDER user ID: {spider_id}")

    existing = get_existing_off_claims()
    print(f"Existing OFF claims in DB: {len(existing)}")

    products = fetch_products(config)
    print(f"\nLoaded {len(products)} products total")

    claims = generate_claims(products, config, spider_id)
    print(f"Generated {len(claims)} claims")

    # Dedup against existing claims
    new_claims = []
    skipped = 0
    for claim in claims:
        key = (claim["subject"], claim["object"], claim["claim"])
        if key in existing:
            skipped += 1
        else:
            new_claims.append(claim)
            existing.add(key)  # prevent duplicates within this batch too

    print(f"After dedup: {len(new_claims)} new, {skipped} skipped")

    if not new_claims:
        print("No new claims to insert.")
        return

    # Insert claims one at a time using lib/db.insert_data (returns id, handles quoting)
    inserted = 0
    errors = 0
    for claim in new_claims:
        try:
            claim_id = insert_data("Claim", claim)
            if claim_id:
                inserted += 1
            else:
                errors += 1
                print(f"  Warning: insert returned no ID for {claim['statement'][:60]}...")
        except Exception as e:
            errors += 1
            print(f"  Error inserting claim: {e}")

    print(f"\n=== Summary ===")
    print(f"Products fetched: {len(products)}")
    print(f"Claims generated: {len(claims)}")
    print(f"Duplicates skipped: {skipped}")
    print(f"Claims inserted: {inserted}")
    if errors:
        print(f"Errors: {errors}")


if __name__ == "__main__":
    main()
