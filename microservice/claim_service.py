from flask import Flask, jsonify, request
from claims_to_nodes.pipe import process_targeted
import logging
import os
from dotenv import load_dotenv
from config import config
import psycopg2
import traceback
from datetime import datetime

# Set up logging to both file and console
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_file = os.path.join(log_directory, f"service_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get environment or default to development
env = os.environ.get('FLASK_ENV', 'development')
app = Flask(__name__)
app.config.from_object(config[env])

@app.route('/process_claim/<claim_id>', methods=['POST'])
def process_claim(claim_id):
    logger.info(f"Starting to process claim {claim_id}")
    try:
        logger.debug(f"Database URI: {app.config['DATABASE_URI']}")
        logger.info("Attempting database connection")
        
        # Test database connection first
        conn = psycopg2.connect(app.config['DATABASE_URI'])
        logger.info("Database connection successful")
        conn.close()
        
        # Process the claim synchronously
        logger.info(f"Processing claim with ID: {claim_id}")
        process_targeted(claim_id)
        logger.info(f"Successfully processed claim {claim_id}")
        
        return jsonify({
            "status": "success",
            "message": "Claim processed successfully",
            "claim_id": claim_id
        }), 200
    except Exception as e:
        logger.error(f"Error processing claim {claim_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "claim_id": claim_id
        }), 500

@app.route('/test-db', methods=['GET'])
def test_db():
    logger.info("Testing database connection")
    try:
        logger.debug(f"Attempting to connect with URI: {app.config['DATABASE_URI']}")
        conn = psycopg2.connect(app.config['DATABASE_URI'])
        cur = conn.cursor()
        
        cur.execute('SELECT version();')
        version = cur.fetchone()
        
        cur.close()
        conn.close()
        
        logger.info("Database test successful")
        return jsonify({
            "status": "success",
            "message": "Database connection successful",
            "version": version[0]
        }), 200
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check requested")
    return jsonify({
        "status": "healthy",
        "environment": env,
        "database_uri": app.config['DATABASE_URI']
    }), 200

if __name__ == '__main__':
    port = app.config['PORT']
    host = app.config['HOST']
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Environment: {env}")
    logger.info(f"Database URI: {app.config['DATABASE_URI']}")
    logger.info(f"Log file location: {log_file}")
    app.run(host=host, port=port)