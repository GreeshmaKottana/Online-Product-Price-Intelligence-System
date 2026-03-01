from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allows your React app to make requests to this API

@app.route('/')
def hello_world():
    return jsonify({"message": "Backend is running successfully!"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)