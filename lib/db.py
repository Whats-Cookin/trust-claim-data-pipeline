import psycopg2
import json

from lib.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

# Connect to the PostgreSQL database
def get_conn():
    global conn
    try:
        conn.status  # Check if the connection is open
    except (NameError, AttributeError, psycopg2.OperationalError):
        # Reconnect if the connection is closed or doesn't exist
        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
    return conn


def get_claim(claim_id):
    query = """SELECT id, subject, claim, object, statement, "effectiveDate", 
               "sourceURI", "howKnown", "dateObserved", "digestMultibase", author, 
               curator, aspect, score, stars, amt, unit, "howMeasured", 
               "intendedAudience", "respondAt", confidence, "issuerId", 
               "issuerIdType", "claimAddress", proof 
               FROM "Claim" WHERE id = %s"""
    return execute_sql_query(query, (claim_id,))


def get_credential(credential_id):
    query = """SELECT id, context, type, issuer, "issuanceDate", 
                      "expirationDate", "credentialSubject", proof, "sameAs", 
                      "createdAt", "updatedAt"
               FROM "Credential" WHERE id = %s"""
    
    result = execute_sql_query(query, (credential_id,))

    if result:
        # Convert JSON fields from dict to string if necessary
        json_fields = ["context", "type", "issuer", "credentialSubject", "proof", "sameAs"]
        for field in json_fields:
            if field in result and isinstance(result[field], dict):
                result[field] = json.dumps(result[field])  # Convert dict to JSON string
                
    return result


def unprocessed_entities_generator(entity_type="claim"):
    table_name = '"Claim"' if entity_type == "claim" else '"Credential"'
    id_column = "claimId" if entity_type == "claim" else "credentialId"

    with get_conn().cursor() as cur:
        cur.execute(f'SELECT MAX("{id_column}") FROM "Edge"')
        latest_entity_id = cur.fetchone()[0] or 0  # Default to 0 if None

        query = f'SELECT * FROM {table_name} WHERE id > %s'
        cur.execute(query, (latest_entity_id,))

        columns = [desc[0] for desc in cur.description]
        while True:
            rows = cur.fetchmany()
            if not rows:
                break
            for row in rows:
                yield dict(zip(columns, row))


def unpublished_entities_generator(entity_type="claim"):
    table_name = '"Claim"' if entity_type == "claim" else '"Credential"'
    address_column = "claimAddress" if entity_type == "claim" else "credentialAddress"

    query = f'SELECT * FROM {table_name} WHERE "{address_column}" IS NULL OR "{address_column}" = \'\''
    with get_conn().cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        while True:
            rows = cur.fetchmany()
            if not rows:
                break
            for row in rows:
                yield dict(zip(columns, row))


def update_entity_address(entity_type, entity_id, entity_address):
    """Update the claimAddress or credentialAddress field"""
    if not entity_id:
        raise ValueError("Cannot update without an entity ID")
    
    table_name = '"Claim"' if entity_type == "claim" else '"Credential"'
    address_column = "claimAddress" if entity_type == "claim" else "credentialAddress"

    query = f'UPDATE {table_name} SET "{address_column}" = %s WHERE id = %s'
    execute_sql_query(query, (entity_address, entity_id))


def execute_sql_query(query, params):
    with get_conn().cursor() as cur:
        cur.execute(query, params)
        result = cur.fetchone()
        conn.commit()
        if result is not None:
            col_names = [desc[0] for desc in cur.description]
            return dict(zip(col_names, result))
        return None


def insert_data(table, data):
    conn = get_conn()
    quoted_keys = ['"' + key + '"' for key in data.keys()]
    query = f'INSERT INTO "{table}" ({", ".join(quoted_keys)}) VALUES ({", ".join(["%s"] * len(data))}) RETURNING id;'
    return execute_sql_query(query, tuple(data.values()))["id"]


def insert_node(node):
    """Insert a Node into the database."""
    return insert_data(table="Node", data=node)


def insert_edge(edge):
    """Insert an Edge into the database."""
    return insert_data(table="Edge", data=edge)


def get_node_by_uri(node_uri):
    """Retrieve a Node from the database by its nodeUri value."""
    query = """SELECT id, "nodeUri", name, "entType", descrip, image, thumbnail
               FROM "Node" WHERE "nodeUri" = %s"""
    return execute_sql_query(query, (node_uri,))


def get_edge_by_endpoints(start_node_id, end_node_id, entity_id):
    """Retrieve an Edge from the database by the IDs of its start and end Nodes."""
    query = """SELECT id, "startNodeId", "endNodeId", label, thumbnail, "claimId"
               FROM "Edge" WHERE "startNodeId" = %s AND "endNodeId" = %s AND "claimId" = %s"""
    return execute_sql_query(query, (start_node_id, end_node_id, entity_id))


def del_entity(entity_type, entity_id):
    """Delete a Claim or Credential along with its associated edges."""
    if not entity_id:
        raise ValueError("A non-zero, non-null entity ID is required")
    
    table_name = '"Claim"' if entity_type == "claim" else '"Credential"'
    id_column = "claimId" if entity_type == "claim" else "credentialId"

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(f'DELETE FROM "Edge" WHERE "{id_column}" = %s', (entity_id,))
        cur.execute(f'DELETE FROM {table_name} WHERE id = %s', (entity_id,))
        conn.commit()
