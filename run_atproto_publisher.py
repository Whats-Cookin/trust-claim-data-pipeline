"""Entry point for publishing unpublished claims to ATProto PDS.

Usage:
    cd /opt/shared/repos/trust-claim-data-pipeline
    python run_atproto_publisher.py
"""

from claims_to_atproto import publish_unpublished

publish_unpublished()