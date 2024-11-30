-- Create Claim table
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

-- Create Node table
CREATE TABLE IF NOT EXISTS "Node" (
    id SERIAL PRIMARY KEY,
    "nodeUri" TEXT UNIQUE,
    name TEXT,
    "entType" TEXT,
    descrip TEXT,
    image TEXT,
    thumbnail TEXT
);

-- Create Edge table
CREATE TABLE IF NOT EXISTS "Edge" (
    id SERIAL PRIMARY KEY,
    "startNodeId" INTEGER REFERENCES "Node"(id),
    "endNodeId" INTEGER REFERENCES "Node"(id),
    label TEXT,
    thumbnail TEXT,
    "claimId" INTEGER REFERENCES "Claim"(id)
);
