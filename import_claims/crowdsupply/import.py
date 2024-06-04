from datetime import datetime, timedelta
import pandas as pd
import sys
from dotenv import dotenv_values

config = dotenv_values("../.env")

def extract_config_data(row, backer, project_url, claim):
    effective_date = row['Date Funded or Days to be funded']
    # Check if the effective_date is a date or an integer (days to be funded)
    try:
        effective_date = datetime.strptime(effective_date, '%b %d %Y').strftime('%Y-%m-%d')
    except ValueError:
        # Calculate the effective date based on days to be funded
        effective_date = (datetime.strptime(row['Date Scraped'], '%Y-%m-%d') - timedelta(days=int(effective_date))).strftime('%Y-%m-%d')

    statement = f"{backer} {claim} {project_url}"

    config_data = {
        "filename": csv_filename,
        "subject": backer,
        "subject_type": "",
        "source": project_url,
        "statement": statement,
        "claim": claim,
        "howknown": "WEB_DOCUMENT",
        "effectiveDate": effective_date,
        "confidence": 0.9
    }

    return config_data

csv_filename = "cleaned_crowdsupply_data.csv"
claim = "funded_for_a_purpose"

try:
    df = pd.read_csv(csv_filename)
except FileNotFoundError:
    print(f"Error: File not found. Is '{csv_filename}' a valid path?")
    sys.exit(1)

values = []

for index, row in df.iterrows():
    backers = [b.strip() for b in row['Backers'].split(',')]
    project_url = row['Project URL']
    
    for backer in backers:
        if backer:  # Ensure the backer is not an empty string
            config_data = extract_config_data(row, backer, project_url, claim)
            values.append((
                config_data["subject"],
                config_data["source"],
                config_data["statement"],
                config_data["claim"],
                config_data["howknown"],
                config_data.get("confidence", 0),
                config_data.get("effectiveDate"),
                "http://trustclaims.whatscookin.us/users/{}".format(config.get('spider_id', 1)),
                "URL"
            ))
