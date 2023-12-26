from ..claims_to_nodes.pipe import process_single_claim
from flask import Flask, request, render_template, jsonify

app = Flask(__name__, template_folder='templates')

@app.route('/process_raw_claim', methods=['GET'])
def get_claim():
    return render_template('index.html')

@app.route('/process_raw_claim', methods=['POST'])
def process_raw_claim():
    try:
        subject = request.form.get('subject')
        claim = request.form.get('claim')
        how_known = request.form.get('how_known')
        statement = request.form.get('statement')
        source_uri = request.form.get('source_uri')
        confidence = request.form.get('confidence')
        aspect = request.form.get('aspect')
        review_rating = request.form.get('review_rating')
        effective_date = request.form.get('effective_date')
        score =  int(confidence)//100 #this is just a test logic to fill in the score

        raw_claim = {
            'subject': subject,
            'claim': claim,
            'how_known': how_known,
            'statement': statement,
            'sourceURI': source_uri,
            'confidence': confidence,
            'aspect': aspect,
            'stars': review_rating,
            'effective_date': effective_date,
            'score':score,
        }

        process_single_claim(raw_claim)
        print(id)
        return jsonify({'status': 'success', 'message': 'Input processed successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

    
if __name__ == '__main__':
    app.run(debug=True)