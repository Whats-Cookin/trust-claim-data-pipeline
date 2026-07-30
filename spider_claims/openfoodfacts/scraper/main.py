"""Open Food Facts API scraper for the spider pipeline.

Fetches product data from the OFF search API and writes raw JSON to the
output directory, following the pattern used by other spiders in spider_claims/.
"""

import json
import os
import sys
import time
from datetime import datetime

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))


def load_config():
    # Config is in the spider root, not in scraper/
    config_path = os.path.join(SCRIPT_DIR, "..", "config.json")
    with open(config_path) as f:
        return json.load(f)


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
    resp.raise_for_status()


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
    """Fetch products, trying search API first then falling back to individual lookups."""
    try:
        products = fetch_products_via_search(config)
        if products:
            return products
    except requests.HTTPError as e:
        print(f"Search API unavailable ({e}), falling back to individual product lookups...")

    return fetch_products_by_barcode(config)


def write_output(products, config):
    """Write scraped products to output directory as JSON."""
    output_dir = os.path.join(SCRIPT_DIR, "..", config.get("output_dir", "data"))
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"off_products_{timestamp}.json")

    with open(output_file, "w") as f:
        json.dump({
            "fetched_at": datetime.utcnow().isoformat(),
            "count": len(products),
            "products": products,
        }, f, indent=2)

    print(f"Wrote {len(products)} products to {output_file}")
    return output_file


def main():
    print("=== Open Food Facts Spider ===")

    config = load_config()
    print(f"Config: {config['max_pages']} page(s), {config['page_size']} per page")
    print(f"Target labels: {config['target_labels']}")

    products = fetch_products(config)
    print(f"\nFetched {len(products)} products total")

    if not products:
        print("No products fetched.")
        return

    output_file = write_output(products, config)
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()