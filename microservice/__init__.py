from logging.config import dictConfig

from flask import Flask, jsonify

from claims_to_nodes.pipe import process_targeted

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

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
