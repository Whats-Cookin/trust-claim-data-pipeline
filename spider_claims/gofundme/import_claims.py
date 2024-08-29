# Note: For the code to execute properly, I've provided a detailed 
# step-by-step installation guide. You can find the setup instructions
# in the following file:
# trust-claim-data-pipeline/spider_claims/gofundme/import_claims_setup.md

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import re

# Print statement for script execution
print("Script execution started.")

# Configure logging
logging.basicConfig(filename='import_claims.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Email Configuration
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
recipient_email = os.getenv("RECIPIENT_EMAIL")

# Database connection settings
DATABASE_URL = os.getenv("DATABASE_URL")

# Function to clean numeric data
def clean_numeric(value):
    try:
        if pd.isna(value) or value.strip() == '':
            return '0'
        cleaned_value = re.sub(r'[^\d.]', '', value)
        if cleaned_value.count('.') > 1:
            parts = cleaned_value.split('.')
            cleaned_value = parts[0] + '.' + ''.join(parts[1:])
        if cleaned_value == '' or cleaned_value == '.':
            return '0'
        float_value = float(cleaned_value)
        return str(float_value)
    except ValueError as ve:
        logging.error(f"ValueError in cleaning numeric value '{value}': {ve}")
        return '0'
    except Exception as e:
        logging.error(f"Failed to clean numeric value '{value}': {e}")
        return '0'

# Function to send email notifications
def send_email(subject, body):
    try:
        print(f"Sending email: {subject}")
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logging.info(f"Email sent: {subject}")
        print(f"Email sent: {subject}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        print(f"Failed to send email: {e}")

# Function to check for new claims and upload to the database
def import_claims():
    print("Starting import process...")
    logging.info("Starting import process...")

    try:
        df = pd.read_csv('/home/am/Documents/Scrapping/python_claim_importer/gofundme_scrap.csv')
        logging.info(f"Loaded {len(df)} rows from CSV.")
        print(f"Loaded {len(df)} rows from CSV.")
    except Exception as e:
        logging.error(f"Failed to load CSV: {e}")
        print(f"Failed to load CSV: {e}")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        logging.info("Connected to the database.")
        print("Connected to the database.")
        new_claims = 0

        for index, row in df.iterrows():
            logging.info(f"Processing row {index + 1}/{len(df)}...")
            print(f"Processing row {index + 1}/{len(df)}...")
            
            # Clean numeric values
            amount_raised = clean_numeric(row['Amount Raised'])
            goal_amount = clean_numeric(row['Goal Amount'])
            donations = clean_numeric(row['Donations'])

            # Skip row if numeric values are invalid or if cleaning resulted in '0'
            if amount_raised == '0' and (pd.isna(row['Amount Raised']) or row['Amount Raised'] == ''):
                logging.warning(f"Skipping row {index + 1} due to invalid Amount Raised: {row}")
                continue
            if goal_amount == '0' and (pd.isna(row['Goal Amount']) or row['Goal Amount'] == ''):
                logging.warning(f"Skipping row {index + 1} due to invalid Goal Amount: {row}")
                continue
            if donations == '0' and (pd.isna(row['Donations']) or row['Donations'] == ''):
                logging.warning(f"Skipping row {index + 1} due to invalid Donations: {row}")
                continue

            try:
                cursor.execute("SELECT * FROM claim WHERE source_url = %s", (row['Source URL'],))
                result = cursor.fetchone()

                if result is None:
                    cursor.execute("""
                        INSERT INTO claim (title, statement, amount_raised, goal_amount, donations, source_url, date_scraped)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row['Title'], row['Statement'], amount_raised, goal_amount,
                        donations, row['Source URL'], row['Date Scraped']
                    ))
                    conn.commit()
                    new_claims += 1
                    logging.info(f"Inserted new claim: {row['Title']}")
                    print(f"Inserted new claim: {row['Title']}")
            except Exception as e:
                logging.error(f"Failed to process claim: {e}")
                print(f"Failed to process claim: {e}")

        cursor.close()
        conn.close()
        logging.info("Database connection closed.")
        print("Database connection closed.")

    except Exception as e:
        logging.error(f"Failed to process claims: {e}")
        print(f"Failed to process claims: {e}")
        return

    # Send email notification
    if new_claims == 0:
        subject = "LinkedTrust: No New Claims This Hour"
        body = "The automated script ran, but no new claims were found in the CSV to upload."
    else:
        subject = f"LinkedTrust: {new_claims} New Claim(s) Added"
        body = f"The automated script successfully added {new_claims} new claim(s) to the database."

    send_email(subject, body)
    logging.info("Import finished and notification sent.")
    print("Import finished and notification sent.")

import_claims()
