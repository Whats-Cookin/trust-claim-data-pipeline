# Python Claim Import Script Set Up

## Setup Virtual Environment ( Optional )

Create and activate a virtual environment to manage dependencies:

```bash
python3 -m venv venv
``` 
Activate the virtual environment:

## On Linux/macOS:
`source venv/bin/activate`

## On Windows:
`venv\Scripts\activate`

## Install Required Libraries

With the virtual environment activated, install the necessary libraries:
`pip install pandas psycopg2 python-dotenv`

## Configure Environment Variables

Create a `.env` file in the root directory of your project with the following content:

SENDER_EMAIL=your_sender_email@example.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=recipient_email@example.com
DATABASE_URL="postgresql://your_db_user:your_db_password@localhost:5432/your_db_name"

```Note: Replace your_sender_email@example.com, your_app_password, recipient_email@example.com, your_db_user, your_db_password, and your_db_name with your actual details. Do not share these credentials publicly.```

## Set Up Cron Job for Automation
To automate the script execution, use cron. Open the crontab editor:

`crontab -e`

Add the following line to run the script daily at midnight (adjust the schedule as needed):

0 0 * * * /path/to/venv/bin/python3 /path/to/your_script.py >> /path/to/logfile.log 2>&1

Replace /path/to/venv, /path/to/your_script.py, and /path/to/logfile.log with the actual paths.

as an example heres a file path to my machine:- 

0 0 * * * /home/am/Documents/Scrapping/python_claim_importer/venv/bin/python3 /home/am/Documents/Scrapping/python_claim_importer/importClaims.py >> /home/am/Documents/Scrapping/python_claim_importer/logs/import_claims.log 2>&1

## Run the Script Manually for Testing
You can run the script manually to ensure everything is working correctly:
`python3 /path/to/import_claims.py`

