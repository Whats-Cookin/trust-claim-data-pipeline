#!/bin/bash
cd /data/trust-claim-data-pipeline/admin
source venv/bin/activate
exec gunicorn linkedtrust_admin.wsgi:application --bind 127.0.0.1:8001 --workers 2
