import json
from datetime import datetime
import pandas as pd
import re
import psycopg2
import validators
import urllib
import sys
from dotenv import dotenv_values

config = dotenv_values("../.env")


def print_error_and_exit(str):
    print(f"Error: {str}")
    sys.exit(2)


def db_post_one(query, values):
    conn = None
    try:
        conn = psycopg2.connect(config.get("DATABASE_URL"))
        cursor = conn.cursor()

        cursor.execute(query, values)
        conn.commit()
    except (Exception, psycopg2.Error) as error:
        print("Failed insertion: {}".format(error))
        print_error_and_exit(error)
    finally:
        if conn:
            cursor.close()
            conn.close()


def db_post_many(query, values):
    conn = None
    try:
        conn = psycopg2.connect(config.get("DATABASE_URL"))
        cursor = conn.cursor()

        cursor.executemany(query, values)
        conn.commit()
    except (Exception, psycopg2.Error) as error:
        print("Failed insertion: {}".format(error))
        print_error_and_exit(error)
    finally:
        if conn:
            cursor.close()
            conn.close()


def extract_config_data(
    row, subject_from_csv_header, statement_from_csv_header, object_from_csv_header
):
    scraped_meta_str = row[object_from_csv_header].replace("'", '"')
    ipfs_uri_match = re.search(r'"ipfs_uri":\s*"([^"]+)"', scraped_meta_str)

    if ipfs_uri_match:
        ipfs_uri = ipfs_uri_match.group(1)
    else:
        ipfs_uri = ""

    effective_date = datetime.utcfromtimestamp(
        int(row["impact_timeframe_value"].strip("[]").split(",")[0])
    ).strftime("%Y-%m-%d")

    config_data = {
        "filename": csv_filename,
        "subject": row[subject_from_csv_header],
        "subject_type": "ORGANISATION",
        "source": ipfs_uri,
        "statement": row[statement_from_csv_header],
        "claim": "impact",
        "howknown": "WEB_DOCUMENT",
        "effectiveDate": effective_date,
        "confidence": 0,
    }

    return config_data


csv_filename = "hypercert-claim-data.csv"
subject_from_csv_header = "url"
statement_from_csv_header = "description"
object_from_csv_header = "scraped_meta"

try:
    df = pd.read_csv(csv_filename)
except FileNotFoundError:
    print(f"Error: File not found. Is '{csv_filename}' a valid path?")
    sys.exit(1)

query = """INSERT INTO "Claim" (subject, "sourceURI", statement, claim, "howKnown", confidence, "effectiveDate", "issuerId", "issuerIdType") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

values = []

for index, row in df.iterrows():
    config_data = extract_config_data(
        row, subject_from_csv_header, statement_from_csv_header, object_from_csv_header
    )
    values.append(
        (
            config_data["subject"],
            config_data["source"],
            config_data["statement"],
            config_data["claim"],
            config_data["howknown"],
            config_data.get("confidence", 0),
            config_data.get("effectiveDate"),
            "http://trustclaims.whatscookin.us/users/{}".format(
                config.get("spider_id", 1)
            ),
            "URL",
        )
    )

import pdb

pdb.set_trace()
db_post_many(query, values)

# config_data = extract_config_data(csv_filename, subject_from_csv_header, statement_from_csv_header, object_from_csv_header)

# query = """INSERT INTO "Claim" (subject, object, statement, claim, aspect, "howKnown", "reviewRating", source, confidence, "userId", "issuerId", "issuerIdType") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
# values = (
#     config_data["subject"],
#     config_data["object"],
#     config_data["statement"],
#     config_data["claim"],
#     config_data["aspect"],
#     config_data["howknown"],
#     config_data.get("score", 1.0),
#     config_data.get("source_from_csv_header", ""),
#     config_data.get("confidence", 0.9),
#     1,
#     f"http://trustclaims.whatscookin.us/users/{config.get('spider_id')}",
#     "URL"
# )

# db_post_one(query, values)

print("Data has been inserted into the PostgreSQL database.")
