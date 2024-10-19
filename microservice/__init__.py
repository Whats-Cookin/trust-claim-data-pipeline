from flask import Flask, jsonify

from claims_to_nodes.pipe import process_targeted

app = Flask(__name__)


@app.route("/process_claim/<claim_id>", methods=["POST"])
def process_claim(claim_id):
    try:
        process_targeted(claim_id)
        return jsonify({"message": "Claim processed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
