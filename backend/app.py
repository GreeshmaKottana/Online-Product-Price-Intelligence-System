from dotenv import load_dotenv
import os

load_dotenv()

import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
from preprocessing import process_image
from model_engine import identify_product
from scraper import fetch_all_prices
from price_engine import compare_prices

app = Flask(__name__)
# Enable CORS so the React frontend can talk to this API
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# --- Configuration ---
# Create an 'uploads' folder in the same directory as app.py
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
# Allowed file extensions per Task 3 requirements
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# File size validation: Max 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 

# Ensure the upload directory exists when the app starts
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from database import db

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Endpoints ---
@app.route('/api/upload-image', methods=['POST'])
def upload_image():

    if 'image' not in request.files:
        return jsonify({
            "status": "error",
            "message": "No image uploaded"
        }), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({
            "status": "error",
            "message": "Empty filename"
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "status": "error",
            "message": "Invalid file format"
        }), 400

    image_id = str(uuid.uuid4())

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(f"{image_id}.{ext}")

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:

        file.save(filepath)

        img_normalized, img_enhanced = process_image(filepath)

        enhanced_filename = f"enhanced_{filename}"
        enhanced_filepath = os.path.join(app.config['UPLOAD_FOLDER'], enhanced_filename)

        cv2.imwrite(enhanced_filepath, cv2.cvtColor(img_enhanced, cv2.COLOR_RGB2BGR))

        ml_results = identify_product(filepath)

        if ml_results["status"] != "success":
            return jsonify({
                "status": "error",
                "message": "AI prediction failed"
            }), 500

        keyword = ml_results["analysis"]["category"]

        if not keyword or len(keyword) < 2:
            return jsonify({
                "status": "error",
                "message": "Invalid detected product"
            }), 400

        price_results = fetch_all_prices(keyword)

        comparison = compare_prices(price_results)

        return jsonify({
            "status": "success",
            "analysis": ml_results,
            "price_results": price_results,
            "comparison": comparison
        })

        from crud import create_product, create_price, save_search

        save_search("anonymous", keyword)

        product = create_product(
            name=keyword,
            category=keyword,
            image_url=filename
        )

        for item in price_results:

            price_raw = item.get("price")

            if not price_raw:
                continue

            try:
                price_clean = str(price_raw)
                price_clean = price_clean.replace("₹", "")
                price_clean = price_clean.replace(",", "")
                price_clean = price_clean.replace("$", "")
                price_clean = price_clean.strip()

                price_value = float(price_clean)

            except Exception:
                continue

            create_price(
                product.product_id,
                item.get("store"),
                price_value,
                item.get("url")
            )

        return jsonify({
            "status": "success",
            "analysis": ml_results,
            "price_results": price_results
        }), 201

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/products", methods=["GET"])
def get_products():

    from database import Product

    products = Product.query.all()

    result = []

    for p in products:
        result.append({
            "product_id": p.product_id,
            "name": p.name,
            "category": p.category,
            "image_url": p.image_url
        })

    return jsonify(result)

@app.route("/api/prices/<int:product_id>", methods=["GET"])
def get_prices(product_id):

    from database import Price

    prices = Price.query.filter_by(product_id=product_id).all()

    result = []

    for p in prices:
        result.append({
            "store": p.store_name,
            "price": p.price,
            "timestamp": p.timestamp,
            "url": p.product_url
        })

    return jsonify(result)

@app.route("/api/search-history", methods=["GET"])
def get_search_history():

    from database import db, SearchHistory

    searches = db.session.query(SearchHistory).order_by(SearchHistory.timestamp.desc()).all()

    result = []

    for s in searches:
        result.append({
            "search_id": s.search_id,
            "user_id": s.user_id,
            "query": s.query,
            "timestamp": str(s.timestamp)
        })

    return jsonify(result)

@app.route("/api/search-history/<int:search_id>", methods=["DELETE"])
def delete_search(search_id):

    from database import db, SearchHistory

    search = SearchHistory.query.get(search_id)

    if not search:
        return jsonify({"error": "Search not found"}), 404

    db.session.delete(search)
    db.session.commit()

    return jsonify({"message": "Search deleted successfully"})

# Global Error Handler: Triggers automatically if a file exceeds 10MB
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "status": "error", 
        "message": "File exceeds the 10MB size limit."
    }), 413

if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)