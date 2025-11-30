#!/bin/bash
cd /data/trust-claim-data-pipeline
export PYTHONPATH=/data/trust-claim-data-pipeline
source venv/bin/activate
python microservice/__init__.py
