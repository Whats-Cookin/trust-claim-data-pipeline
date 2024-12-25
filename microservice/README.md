# Getting Started

From the root directory of the project, start `venv`

```bash
py -m venv venv
sudo chmod +x venv/bin/activate
source venv/bin/activate
```

Install requirements

```bash
pip install -r requirements.txt
```

Run the application for development

```bash
flask --app microservice run

# To run on a different port:
# flask --app microservice run --port 3000
```

**Or** to run for production

```bash
python __init__.py
```

## Simple Deployment

```
python3 -m venv venv
pip install -r requirements.txt
pm2 start venv/bin/python --name "trust-claim-data-pipeline" -- -m flask --app microservice run
pm2 save
```
