"""Spider entry point for Open Food Facts.

Fetches product data from the OFF API and outputs raw JSON to the data/
directory. The importer (import_claims/openfoodfacts/) consumes this output
to generate LinkedTrust claims.

Usage:
    cd /opt/shared/repos/trust-claim-data-pipeline
    python spider_claims/openfoodfacts/run.py
"""

from scraper.main import main

if __name__ == "__main__":
    main()