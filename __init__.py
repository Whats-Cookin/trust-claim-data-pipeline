from flask import Flask, jsonify

from claims_to_nodes.pipe import process_targeted
from microservice.logconfig import *

app = Flask(__name__)


@app.route("/process_entity/<entity_type>/<entity_id>", methods=["POST"])
def process_entity(entity_type, entity_id):
    if entity_type not in ["claim", "credential"]:
        return jsonify({"error": "Invalid entity type. Must be 'claim' or 'credential'"}), 400

    try:
        app.logger.info(f'Processing {entity_type} with id "{entity_id}"')
        process_targeted(entity_id, entity_type)
        return jsonify({"message": f"{entity_type.capitalize()} processed successfully"}), 200
    except Exception as e:
        app.logger.error(f'Failed to process {entity_type} with id: "{entity_id}" : {str(e)}')
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    from waitress import serve
    from lib.config import APP_PORT

    serve(app, host="0.0.0.0", port=APP_PORT or 5000)
