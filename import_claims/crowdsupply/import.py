import validators
import urllib
import pandas as pd
import sys
import psycopg2
import json
from dotenv import dotenv_values
from datetime import datetime

config = dotenv_values("../.env")

def print_error_and_exit(str):
    print(f"Error: {str}")
    sys.exit(2)


def get_db_connection():
    conn = psycopg2.connect('postgresql://postgres:lekan2904.@user:5432/postgres')
    return conn


def db_get_one(query: str):
    conn = None
    res = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(query)
        res = cur.fetchone()

        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return res


# def db_post_many(query, values):
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.executemany(query, values)
#         conn.commit()

#     except (Exception, psycopg2.Error) as error:
#         print("Failed insertion: {}".format(error))

#     finally:
#         if conn:
#             cursor.close()
#             conn.close()

def db_post_many(query, values):
    conn = None
    try:
        # Replace with your actual database URL
        conn = psycopg2.connect('postgresql://user:lekan2904.@localhost:5432/postgres')
        cur = conn.cursor()
        
        # Execute the given query with the provided values
        cur.executemany(query, values)
        
        # Commit the transaction
        conn.commit()
        
        # Close the cursor
        cur.close()
        
    except Exception as error:
        print(f"Error: {error}")
        
    finally:
        # Ensure the connection is closed even if an error occurs
        if conn is not None:
            conn.close()


def main():
    settings = None

    try:
        with open("config.json") as f:
            settings = json.load(f)
    except Exception as e:
        print_error_and_exit(str(e))

    filename = settings.get("filename")
    subject = settings.get("subject")
    subject_from_csv_header = settings.get("subject_from_csv_header")
    claim_object = settings.get("object")  # object is a python built-in keyword
    object_from_csv_header = settings.get("object_from_csv_header")
    statement = settings.get("statement")
    statement_from_csv_header = f'Received crowdfunding for {settings.get("statement_from_csv_header")}'
    claim = settings.get("claim")
    aspect = settings.get("aspect")
    amt_from_csv_header = settings.get("amt_from_csv_header")
    unit_from_csv_header = settings.get("unit_from_csv_header")
    date_from_csv_header = settings.get("date_from_csv_header")

    # note in this version rating is NOT handled

    fixed_source = settings.get("source")
    source_from_csv_header = settings.get("source_from_csv_header")
    confidence = settings.get("confidence")
    how_known = settings.get("howknown")

    if not (filename):
        print_error_and_exit('"filename" is a required field')
    if not (subject or subject_from_csv_header):
        print_error_and_exit('Either "subject" or "subject_from_csv_header" field is required')
    if not (claim_object or object_from_csv_header or fixed_source or source_from_csv_header):
        print_error_and_exit('Either "object" or "object_from_csv_header" or "source" field is required')
    if not (claim):
        print_error_and_exit('"claim" is a required field')

    try:
        df = pd.read_csv(filename, on_bad_lines='skip')
    except FileNotFoundError:
        print_error_and_exit(f"Error: File not found. Is \"{filename}\" a valid path?")
    except Exception as e:
        print_error_and_exit(f"{str(e)}")

    # spider = db_get_one("""SELECT * FROM "User" WHERE name='SPIDER'""")
    # if spider:
    #    spider_id = spider[0]
    # else:
    #    spider_id = 1

    values = []
    for _, row in df.iterrows():
        if date_from_csv_header:
            sub = subject or row[subject_from_csv_header]
            obj = claim_object or row.get(object_from_csv_header)
            source = fixed_source or row.get(source_from_csv_header)
            if obj:
               obj_is_url = validators.url(obj)
            else:
               obj = ''
               obj_is_url = False

            if obj and not obj_is_url:
                obj = "http://trustclaims.whatscookin.us/local/company/" + urllib.parse.quote(obj)

            stmt = row.get(statement_from_csv_header, '') or statement
            amt = row.get(amt_from_csv_header, 0)
            amt = int(amt.replace(",",""))
            unit = row.get(unit_from_csv_header, 'USD')
            effective_date = datetime.strptime(row.get(date_from_csv_header, ''), '%b %d %Y').strftime('%Y-%m-%d')
            issuer_id = f"http://trustclaims.whatscookin.us/users/{subject}"

            values.append((sub, obj, stmt, claim, aspect, how_known, amt, unit, effective_date,
                           source, confidence, issuer_id, 'URL'))
        else:
            print("Error, date_from_csv_header is missing")

   # import pdb; pdb.set_trace()
        query = """INSERT INTO "Claim" (subject, object, statement, claim, aspect, "howKnown", amt, unit, "effectiveDate", "sourceURI", confidence, "issuerId", "issuerIdType") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        db_post_many(query, values)
    print("Successfully imported")


if __name__ == "__main__":
    main()
