# import_hypercerts.py

Imports real hypercerts from the live Hypercerts GraphQL API as LinkedClaims.

- One hypercert -> one claim (`claim=impact`, self-asserted by minter, `howKnown=WEB_DOCUMENT`, confidence 0.5) + an `Image` row (the hypercert card) so claims are visual.
- Always linked to source: `subject` & `sourceURI` = web-loadable hypercert page (`app.hypercerts.org/hypercerts/<id>`); IPFS metadata CID in `digestMultibase`; project site in `object`.
- Junk/test entries are filtered out; idempotent on `subject`+`claim`.
- DB creds from repo `.env` (targets `dev_linkedtrust`). Run: `python3 import_hypercerts.py [N]`.

Supersedes the earlier CSV-based `import.py` (which required a scraped CSV and had a debug breakpoint); kept for reference.
