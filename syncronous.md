# Synchronous Claim Processing Implementation Documentation

## Original Problem (from Golda)
> "The problem is that the claim is not created synchronously, it is my fault really because the claim creation is in python, not node, we need to set up a microservice for this."

## Key Issues Identified
1. Users can't see their claims immediately after creation
2. Claims are processed asynchronously via crontab
3. Frontend and claim processing (Python) are not integrated in real-time

## Implementation Summary

### 1. Database Setup
Created required PostgreSQL tables:
```sql
CREATE TABLE IF NOT EXISTS "Claim" (
    id SERIAL PRIMARY KEY,
    subject TEXT,
    claim TEXT,
    object TEXT,
    statement TEXT,
    "effectiveDate" TIMESTAMP,
    "sourceURI" TEXT,
    "howKnown" TEXT,
    "dateObserved" TIMESTAMP,
    "digestMultibase" TEXT,
    author TEXT,
    curator TEXT,
    aspect TEXT,
    score FLOAT,
    stars INTEGER,
    amt FLOAT,
    unit TEXT,
    "howMeasured" TEXT,
    "intendedAudience" TEXT,
    "respondAt" TEXT,
    confidence FLOAT,
    "issuerId" TEXT,
    "issuerIdType" TEXT,
    "claimAddress" TEXT,
    proof TEXT
);

CREATE TABLE IF NOT EXISTS "Node" (
    id SERIAL PRIMARY KEY,
    "nodeUri" TEXT UNIQUE,
    name TEXT,
    "entType" TEXT,
    descrip TEXT,
    image TEXT,
    thumbnail TEXT
);

CREATE TABLE IF NOT EXISTS "Edge" (
    id SERIAL PRIMARY KEY,
    "startNodeId" INTEGER REFERENCES "Node"(id),
    "endNodeId" INTEGER REFERENCES "Node"(id),
    label TEXT,
    thumbnail TEXT,
    "claimId" INTEGER REFERENCES "Claim"(id)
);

2. Microservice Implementation
Location: microservice/claim_service.py
Key endpoints:

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "environment": env,
        "database_uri": app.config['DATABASE_URI']
    })

# Process claim synchronously
@app.route('/process_claim/<claim_id>', methods=['POST'])
def process_claim(claim_id):
    try:
        process_targeted(claim_id)
        return jsonify({
            "status": "success",
            "message": "Claim processed successfully",
            "claim_id": claim_id
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "claim_id": claim_id
        }), 500
    
3. Database Connection Handling
Location: lib/db.py
Improved database connection handling with context managers:

@contextmanager
def get_conn():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URI'))
        yield conn
    finally:
        if conn is not None:
            conn.close()


Testing
The microservice can be tested using:


# Health check
curl http://localhost:5002/health

# Test database connection
curl http://localhost:5002/test-db

# Process a claim
curl -X POST http://localhost:5002/process_claim/124


Running the Service
# From project root
PYTHONPATH=$PYTHONPATH:. python3 microservice/claim_service.py