import json
import pandas as pd
import re

# Defining the CSV file and the fields to extract
csv_filename = "hypercert-claim-data.csv"
subject_from_csv_header = "name"
statement_from_csv_header = "description"
object_from_csv_header = "scraped_meta"

# Loading the CSV file into a pandas DataFrame
try:
    df = pd.read_csv(csv_filename)
except FileNotFoundError:
    print(f"Error: File not found. Is \"{csv_filename}\" a valid path?")
    exit(1)

# Extract data from the first row of the CSV
first_row = df.iloc[0]

# getting the data for source 
scraped_meta_str = first_row[object_from_csv_header].replace("'", "\"")
ipfs_uri_match = re.search(r'"ipfs_uri":\s*"([^"]+)"', scraped_meta_str)

if ipfs_uri_match:
    ipfs_uri = ipfs_uri_match.group(1)
else:
    ipfs_uri = ""

# Create a dictionary with the extracted data
config_data = {
    "filename": csv_filename,
    "subject": "",  # You can set this to a default value or extract it from the CSV
    "subject_from_csv_header": subject_from_csv_header,
    "subject_type": "ORGANISATION",
    "object": ipfs_uri,  # Set "object" to the "ipfs_uri"
    "object_from_csv_header": object_from_csv_header,
    "statement": first_row[statement_from_csv_header],  # Set statement to the "description" value
    "statement_from_csv_header": statement_from_csv_header,
    "claim": "is_vouched_for",
    "aspect": "trust",
    "howknown": "WEB_DOCUMENT",
    "score": 1.0,
    "source_from_csv_header": object_from_csv_header,
    "confidence": 0.9
}

# Update the fields in the dictionary with the extracted data
config_data["subject"] = first_row[subject_from_csv_header]

# Save the updated dictionary to the config.json file
with open("config.json", "w") as config_file:
    json.dump(config_data, config_file, indent=4)

# verify if the process went well
print("config.json has been updated with data from the CSV.")