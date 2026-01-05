from flask import Flask, jsonify, request
from claims_to_nodes.pipe import process_targeted
from microservice.logconfig import *
from lib.db import init_app
from lib.config import APP_PORT

def create_app():
    app = Flask(__name__)

    # Initialize the database connection pool
    init_app(app)

    # New endpoint matching what backend sends
    @app.route("/process-claim", methods=["POST"])
    def process_claim_new():
        try:
            data = request.get_json() or {}
            claim_id = data.get('claim_id')
            subject_entity_type = data.get('subject_entity_type')  # Optional hint

            if not claim_id:
                return jsonify({"error": "claim_id is required"}), 400

            app.logger.info(f'Processing claim with id "{claim_id}"' +
                          (f' with entity hint: {subject_entity_type}' if subject_entity_type else ''))
            process_targeted(claim_id, subject_entity_type)
            return jsonify({"message": "Claim processed successfully"}), 200
        except Exception as e:
            app.logger.error(f'Failed to process claim: {str(e)}')
            return jsonify({"error": str(e)}), 500

    # Keep old endpoint for backwards compatibility
    @app.route("/process_claim/<claim_id>", methods=["POST"])
    def process_claim(claim_id):
        try:
            app.logger.info(f'Processing claim with id "{claim_id}"')
            process_targeted(claim_id)
            return jsonify({"message": "Claim processed successfully"}), 200
        except Exception as e:
            app.logger.error(f'Failed to process claim with id: "{claim_id}" : {str(e)}')
            return jsonify({"error": str(e)}), 500

    return app

if __name__ == "__main__":
    from waitress import serve
    
    # Create the application instance
    app = create_app()
    
    # Run the server
    serve(app, 
          host="0.0.0.0", 
          port=APP_PORT or 5000,
          threads=10,  # Adjust number of threads
          connection_limit=100)  # Max concurrent connections
