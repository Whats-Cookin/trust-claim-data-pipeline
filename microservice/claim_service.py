from flask import Flask, jsonify

app = Flask(__name__)

from ..claims_to_nodes.pipe import process_targeted

@app.route('/process_claim/<claim_id>', methods=['POST'])
def process_claim(claim_id):
    try:
        process_targeted(claim_id)
        return jsonify({"message": "Claim processed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
