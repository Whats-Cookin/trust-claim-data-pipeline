import os
from dotenv import load_dotenv
import psycopg2
from contextlib import contextmanager

load_dotenv()

@contextmanager
def get_conn():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URI'))
        yield conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn is not None:
            conn.close()

def get_claim(claim_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    id, subject, claim, object, statement, 
                    "effectiveDate", "sourceURI", "howKnown", 
                    "dateObserved", "digestMultibase", author, 
                    curator, aspect, score, stars, amt, unit, 
                    "howMeasured", "intendedAudience", "respondAt", 
                    confidence, "issuerId", "issuerIdType", 
                    "claimAddress", proof
                FROM "Claim" 
                WHERE id = %s
            """, (claim_id,))
            
            columns = [desc[0] for desc in cur.description]
            row = cur.fetchone()
            
            if row is None:
                return None
                
            return dict(zip(columns, row))

def unprocessed_claims_generator():
    with get_conn() as conn:
        with conn.cursor() as cur:
            # find latest processed claim
            QUERY_LATEST_CLAIMID = 'SELECT MAX("claimId") FROM "Edge"'
            cur.execute(QUERY_LATEST_CLAIMID)
            latest_claimid = cur.fetchone()[0]
            
            # Read data from the Claim model
            cur.execute("""
                SELECT id, subject, claim, object, statement, \"effectiveDate\", 
                \"sourceURI\", \"howKnown\", \"dateObserved\", \"digestMultibase\", 
                author, curator, aspect, score, stars, amt, unit, \"howMeasured\", 
                \"intendedAudience\", \"respondAt\", confidence, \"issuerId\", 
                \"issuerIdType\", \"claimAddress\", proof 
                FROM \"Claim\" WHERE id > %s
            """, (latest_claimid,))

            columns = [desc[0] for desc in cur.description]
            while True:
                rows = cur.fetchmany()
                if not rows:
                    break
                for row in rows:
                    yield dict(zip(columns, row))

def execute_sql_query(query, params):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            result = cur.fetchone()
            conn.commit()
            if result is not None:
                col_names = [desc[0] for desc in cur.description]
                return dict(zip(col_names, result))
            return None

def update_claim_address(claim_id, claim_address):
    """ Update the claimAddress field of a claim """
    if not claim_id:
        raise Exception("Cannot update without a claim id")
    with get_conn() as conn:
        with conn.cursor() as cur:
            query = f"UPDATE \"Claim\" set \"claimAddress\" = %s where id = %s"
            cur.execute(query, (claim_address, claim_id))
            conn.commit()

def insert_data(table, data):
    quoted_keys = ['\"' + key + '\"' for key in data.keys()]
    query = f"INSERT INTO \"{table}\" ({', '.join(quoted_keys)}) VALUES ({', '.join(['%s']*len(data))}) RETURNING id;"
    try:
        return execute_sql_query(query, tuple(data.values()))['id']
    except Exception as e:
        print(f"Error inserting data: {str(e)}")
        raise

def insert_node(node):
    """Insert a Node into the database."""
    return insert_data(table='Node', data=node)

def insert_edge(edge):
    """Insert an Edge into the database."""
    return insert_data(table='Edge', data=edge)

def get_node_by_uri(node_uri):
    """Retrieve a Node from the database by its nodeUri value."""
    select_node_sql = """
        SELECT id, \"nodeUri\", name, \"entType\", descrip, image, thumbnail
        FROM \"Node\"
        WHERE \"nodeUri\" = %s;
    """
    try:
        row = execute_sql_query(select_node_sql, (node_uri,))
    except Exception as e:
        print(f"Error getting node: {str(e)}")
        raise
    
    if row is None:
        print(f"{node_uri} not found in db")
        return None
        
    return {
        'id': row['id'],
        'nodeUri': row['nodeUri'],
        'name': row['name'],
        'entType': row['entType'],
        'descrip': row['descrip'],
        'image': row['image'],
        'thumbnail': row['thumbnail']
    }

def get_edge_by_endpoints(start_node_id, end_node_id, claim_id):
    """Retrieve an Edge from the database by the IDs of its start and end Nodes."""
    select_edge_sql = """
        SELECT id, \"startNodeId\", \"endNodeId\", label, thumbnail, \"claimId\"
        FROM \"Edge\"
        WHERE \"startNodeId\" = %s AND \"endNodeId\" = %s AND \"claimId\" = %s;
    """
    row = execute_sql_query(select_edge_sql, (start_node_id, end_node_id, claim_id))
    if row is None:
        return None

    return {
        'id': row['id'],
        'startNodeId': row['startNodeId'],
        'endNodeId': row['endNodeId'],
        'label': row['label'],
        'thumbnail': row['thumbnail'],
        'claimId': row['claimId']
    }

def del_claim(claim_id):
    if not claim_id:
        raise ValueError("A non-zero non-null claim id is required")

    with get_conn() as conn:
        with conn.cursor() as cur:
            # delete the edges related to the claim
            cur.execute('DELETE FROM "Edge" WHERE "claimId" = %s', (claim_id,))
            # delete the claim
            cur.execute('DELETE FROM "Claim" WHERE id = %s', (claim_id,))
            conn.commit()