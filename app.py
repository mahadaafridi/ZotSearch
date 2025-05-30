from flask import Flask, request, jsonify
from search import Search
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/search": {"origins": "http://localhost:8000"}})

search_engine = Search(
    index_dir = "small_dev",
    doc_id_file = "small_dev_doc_id.jsonl"
)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"error": "Please provide a valid query"}), 400

    try:
        results = search_engine.search(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)