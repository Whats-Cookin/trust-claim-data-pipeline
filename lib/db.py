import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
try:
    from flask import g, current_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from lib.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

# Global pool for non-Flask contexts (like cron jobs)
_global_pool = None

def get_pool():
    """Get or create the connection pool for both Flask and non-Flask contexts"""
    global _global_pool
    
    if FLASK_AVAILABLE and current_app:
        # If we're in a Flask context, use g
        from flask import g
        if not hasattr(g, 'db_pool'):
            g.db_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
        return g.db_pool
    else:
        # We're not in a Flask context (e.g., cron job)
        if _global_pool is None:
            _global_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
        return _global_pool

def cleanup():
    """Cleanup function for non-Flask contexts"""
    global _global_pool
    if _global_pool is not None:
        _global_pool.closeall()
        _global_pool = None

def init_app(app):
    """Initialize the Flask application with database handling"""
    def close_pool(e=None):
        from flask import g
        pool = getattr(g, 'db_pool', None)
        if pool is not None:
            pool.closeall()
            g.pop('db_pool', None)
            
    app.teardown_appcontext(close_pool)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        if not conn.closed:
            conn.commit()  # Ensure any pending transaction is committed
            pool.putconn(conn)

@contextmanager
def get_db_cursor():
    """Context manager for database cursors"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            yield cursor

def get_claim(claim_id):
    with get_db_cursor() as cur:
        cur.execute(
            'SELECT id, subject, claim, object, statement, "effectiveDate", "sourceURI", "howKnown", "dateObserved", "digestMultibase", author, curator, aspect, score, stars, amt, unit, "howMeasured", "intendedAudience", "respondAt", confidence, "issuerId", "issuerIdType", "claimAddress", proof FROM "Claim" WHERE id = %s',
            (claim_id,)
        )
        columns = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        return dict(zip(columns, row)) if row else None

def unprocessed_claims_generator():
    with get_db_cursor() as cur:
        # find latest processed claim
        QUERY_LATEST_CLAIMID = 'SELECT MAX("claimId") FROM "Edge"'
        cur.execute(QUERY_LATEST_CLAIMID)
        latest_claimid = cur.fetchone()[0] or 0
        
        # Read data from the Claim model
        cur.execute(
            'SELECT id, subject, claim, object, statement, "effectiveDate", "sourceURI", "howKnown", "dateObserved", "digestMultibase", author, curator, aspect, score, stars, amt, unit, "howMeasured", "intendedAudience", "respondAt", confidence, "issuerId", "issuerIdType", "claimAddress", proof FROM "Claim" WHERE id > %s',
            (latest_claimid,)
        )
        
        columns = [desc[0] for desc in cur.description]
        while True:
            rows = cur.fetchmany(1000)  # Fetch in batches of 1000
            if not rows:
                break
            for row in rows:
                yield dict(zip(columns, row))

def unpublished_claims_generator():
    with get_db_cursor() as cur:
        cur.execute(
            'SELECT id, subject, claim, object, statement, "effectiveDate", "sourceURI", "howKnown", "dateObserved", "digestMultibase", author, curator, aspect, score, stars, amt, unit, "howMeasured", "intendedAudience", "respondAt", confidence, "issuerId", "issuerIdType", "claimAddress", proof FROM "Claim" WHERE "claimAddress" is NULL or "claimAddress" = \'\''
        )
        columns = [desc[0] for desc in cur.description]
        while True:
            rows = cur.fetchmany(1000)  # Fetch in batches of 1000
            if not rows:
                break
            for row in rows:
                yield dict(zip(columns, row))

def execute_sql_query(query, params=None):
    with get_db_cursor() as cur:
        cur.execute(query, params)
        result = cur.fetchone()
        if result is not None:
            col_names = [desc[0] for desc in cur.description]
            return dict(zip(col_names, result))
        return None

def update_claim_address(claim_id, claim_address):
    """Update the claimAddress field of a claim"""
    if not claim_id:
        raise Exception("Cannot update without a claim id")
    with get_db_cursor() as cur:
        cur.execute(
            'UPDATE "Claim" SET "claimAddress" = %s WHERE id = %s',
            (claim_address, claim_id)
        )

def insert_data(table, data):
    quoted_keys = ['"' + key + '"' for key in data.keys()]
    query = f'INSERT INTO "{table}" ({", ".join(quoted_keys)}) VALUES ({", ".join(["%s"]*len(data))}) RETURNING id;'
    result = execute_sql_query(query, tuple(data.values()))
    return result['id'] if result else None

def insert_node(node):
    """Insert a Node into the database."""
    return insert_data("Node", node)

def insert_edge(edge):
    """Insert an Edge into the database."""
    return insert_data("Edge", edge)

def get_node_by_uri(node_uri):
    """Retrieve a Node from the database by its nodeUri value."""
    select_node_sql = """
        SELECT id, "nodeUri", name, "entType", descrip, image, thumbnail
        FROM "Node"
        WHERE "nodeUri" = %s;
    """
    row = execute_sql_query(select_node_sql, (node_uri,))
    
    if row is None:
        print("{} not found in db".format(node_uri))
        return None
        
    return {
        "id": row["id"],
        "nodeUri": row["nodeUri"],
        "name": row["name"],
        "entType": row["entType"],
        "descrip": row["descrip"],
        "image": row["image"],
        "thumbnail": row["thumbnail"],
    }

def get_edge_by_endpoints(start_node_id, end_node_id, claim_id):
    """Retrieve an Edge from the database by the IDs of its start and end Nodes."""
    select_edge_sql = """
        SELECT id, "startNodeId", "endNodeId", label, thumbnail, "claimId"
        FROM "Edge"
        WHERE "startNodeId" = %s AND "endNodeId" = %s AND "claimId" = %s;
    """
    row = execute_sql_query(select_edge_sql, (start_node_id, end_node_id, claim_id))
    if row is None:
        return None

    return {
        "id": row["id"],
        "startNodeId": row["startNodeId"],
        "endNodeId": row["endNodeId"],
        "label": row["label"],
        "thumbnail": row["thumbnail"],
        "claimId": row["claimId"],
    }

def del_claim(claim_id):
    if not claim_id:
        raise Exception("A non-zero non-null claim id is required")

    with get_db_cursor() as cur:
        # delete the edges related to the claim
        cur.execute('DELETE FROM "Edge" WHERE "claimId" = %s', (claim_id,))
        cur.execute('DELETE FROM "Claim" WHERE id = %s', (claim_id,))
