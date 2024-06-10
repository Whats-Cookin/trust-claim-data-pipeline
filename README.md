
# Data Pipelines for Trust Claims

This repo includes code for spidering and importing claims, and ALSO for processing 
new claims entered by users.

## For Processing Server

`./run_pipe.py` runs in crontab of the backend server

We are working on a microservice that the Node server running [trust_claim_backend](https://github.com/Whats-Cookin/trust_claim_backend) can call as each new claim is added, currently the crontab just updates every 5 min

### For manual targeted processing

`./target_pipe.py [claim_id]` runs the claims-to-nodes pipeline on just the specified claim id

## For Spider

python code to run separate steps of the pipeline, and later maybe to orchestrate

1) spider and save raw data to be turned into claims

2) clean and normalize the data into an importable format

3) import into signed claims (signed by our spider)

That's all the import data pipeline

Then

4) dedupe, parse and decorate claims into nodes and edges

The nodes and edges will be used to feed the front end views

## Basic Program Architecture
![Program Architecture](./spider-architecture.drawio.png)
