#!/bin/bash
cd /data/trust-claim-data-pipeline
export PYTHONPATH=/data/trust-claim-data-pipeline
venv/bin/python microservice/__init__.py
