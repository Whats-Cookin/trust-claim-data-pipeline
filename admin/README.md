# LinkedTrust Node Admin

Django admin interface for managing Node display properties (name, image, thumbnail).

## Access

- **URL**: https://live.linkedtrust.us/nodeadmin/
- **Username**: admin
- **Password**: changeme123 (CHANGE THIS!)

## What You Can Do

- **Edit Node display properties**: name, descrip, image, thumbnail
- **View Edges and Claims**: read-only reference

## What You Cannot Do

- Create/delete nodes (done by pipeline)
- Create/delete edges (done by pipeline from claims)
- Modify Claims (immutable attestations)
- Change nodeUri (identity of the node)

## Edit Tracking

When you edit a node:
- `editedAt` is automatically set to current timestamp
- `editedBy` is set to your username
- The pipeline will NOT overwrite fields on nodes that have been manually edited

## Local Development

```bash
cd /data/trust-claim-data-pipeline/admin
source venv/bin/activate
python manage.py runserver 8001
```

## Deployment

Runs via pm2:
```bash
pm2 status linkedtrust-admin
pm2 logs linkedtrust-admin
pm2 restart linkedtrust-admin
```

## Change Admin Password

```bash
cd /data/trust-claim-data-pipeline/admin
source venv/bin/activate
python manage.py changepassword admin
```
