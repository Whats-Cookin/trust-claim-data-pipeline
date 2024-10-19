from flask import Flask, jsonify

from claims_to_nodes.pipe import process_targeted
from microservice.logconfig import *

app = Flask(__name__)


@app.route("/process_claim/<claim_id>", methods=["POST"])
def process_claim(claim_id):
    try:
        app.logger.info(f'Signing claim with id "{claim_id}"')
        process_targeted(claim_id)
        return jsonify({"message": "Claim processed successfully"}), 200
    except Exception as e:
        app.logger.error(f'Failed to sign claim with id: "{claim_id}"')
        return jsonify({"error": str(e)}), 500
