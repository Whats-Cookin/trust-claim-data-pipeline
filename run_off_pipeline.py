"""Run the Open Food Facts ingestion pipeline.

Fetches products from OFF API, imports as claims into DB, and processes
claims into nodes/edges.

Usage:
    cd /opt/shared/repos/trust-claim-data-pipeline
    python run_off_pipeline.py
"""

import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run(script_name, description):
    print(f"\n=== {description} ===")
    result = subprocess.run(
        [sys.executable, script_name],
        cwd=SCRIPT_DIR,
    )
    if result.returncode != 0:
        print(f"{description} failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    print(f"{description} succeeded")


def main():
    print("=== Open Food Facts Pipeline ===")

    run("spider_claims/openfoodfacts/run.py", "Spider: fetch products from OFF")
    run("import_claims/openfoodfacts/import_off.py", "Import: convert to claims")
    run("run_pipe.py", "Pipe: process claims into nodes/edges")

    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    main()