import psycopg2

from lib.config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Connect to the PostgreSQL database
def get_conn():
    global conn
    try:
        # check if conn is open
        conn.status
    except (NameError, AttributeError, psycopg2.OperationalError):
        # conn is closed or doesn't exist yet
        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    return conn

def get_claim(claim_id):
    with get_conn().cursor() as cur:
        # Read data from the Claim model
        cur.execute("SELECT id, subject, claim, object, statement, \"effectiveDate\", \"sourceURI\", \"howKnown\", \"dateObserved\", \"digestMultibase\", author, curator, aspect, score, stars, amt, unit, \"howMeasured\", \"intendedAudience\", \"respondAt\", confidence, \"issuerId\", \"issuerIdType\", \"claimAddress\", proof FROM \"Claim\" WHERE id = {}".format(claim_id))
        columns = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        return dict(zip(columns, row)

def unprocessed_claims_generator():
    with get_conn().cursor() as cur:
        # Read data from the Claim model
        # TODO track last date and only process new claims
        cur.execute("SELECT id, subject, claim, object, statement, \"effectiveDate\", \"sourceURI\", \"howKnown\", \"dateObserved\", \"digestMultibase\", author, curator, aspect, score, stars, amt, unit, \"howMeasured\", \"intendedAudience\", \"respondAt\", confidence, \"issuerId\", \"issuerIdType\", \"claimAddress\", proof FROM \"Claim\" WHERE \"createdAt\" > current_timestamp - interval '600 minutes'")
        columns = [desc[0] for desc in cur.description]
        while True:
            rows = cur.fetchmany()
            if not rows:
                break
            for row in rows:
                yield dict(zip(columns, row)) 


def execute_sql_query(query, params):
    with get_conn().cursor() as cur:
        cur.execute(query, params)
        result = cur.fetchone()
        conn.commit()
        if result is not None:
            col_names = [desc[0] for desc in cur.description]
            return dict(zip(col_names, result))
        else:
            return None

def insert_data(table, data):
    conn = get_conn()
    quoted_keys = ['\"' + key + '\"' for key in data.keys()]
    query = f"INSERT INTO \"{table}\" ({', '.join(quoted_keys)}) VALUES ({', '.join(['%s']*len(data))}) RETURNING id;"
    try:
        return execute_sql_query(query, tuple(data.values()))['id']
    except:
        import pdb; pdb.set_trace()

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
    except:
        import pdb ; pdb.set_trace()
    if row is None:
        print("{} not found in db".format(node_uri))
        return None
    node_dict = {
            'id': row['id'],
            'nodeUri': row['nodeUri'],
            'name': row['name'],
            'entType': row['entType'],
            'descrip': row['descrip'],
            'image': row['image'],
            'thumbnail': row['thumbnail']
        }
    return node_dict

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

    edge_dict = {
            'id': row['id'],
            'startNodeId': row['startNodeId'],
            'endNodeId': row['endNodeId'],
            'label': row['label'],
            'thumbnail': row['thumbnail'],
            'claimId': row['claimId']
        }
    return edge_dict


