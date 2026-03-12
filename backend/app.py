import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
from preprocessing import process_image
from model_engine import identify_product
from scraper import fetch_all_prices
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
# Enable CORS so the React frontend can talk to this API
CORS(app, resources={r"/*": {"origins": "*"}})

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

# Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Endpoints ---
@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    # 1. Validate that the request contains the 'image' field
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No image part in the request"}), 400
    
    file = request.files['image']
    
    # 2. Validate that a file was actually selected
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
        
    # 3. Validate the file format
    if not allowed_file(file.filename):
        return jsonify({
            "status": "error", 
            "message": "Invalid file format. Only JPEG, PNG, and WebP are allowed."
        }), 415 # Unsupported Media Type

    # 4. Process and save the valid file
    if file and allowed_file(file.filename):
        # Generate a unique identifier (UUID) for the image
        image_id = str(uuid.uuid4())
        
        # Extract the original extension and create a secure filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        secure_name = secure_filename(f"{image_id}.{ext}")
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
        
        try:
            # 1. Store the original image temporarily
            file.save(filepath)
            
            # 2. TASK 4: Run your OpenCV Preprocessing Pipeline
            img_normalized, img_enhanced = process_image(filepath)
            
            # Save the enhanced version to show the user later
            enhanced_filename = f"enhanced_{secure_name}"
            enhanced_filepath = os.path.join(app.config['UPLOAD_FOLDER'], enhanced_filename)
            cv2.imwrite(enhanced_filepath, cv2.cvtColor(img_enhanced, cv2.COLOR_RGB2BGR))
            
            # 3. TASK 5: Run the ResNet50 Deep Learning Model
            # (We feed it the original filepath because ResNet has strict native requirements)
            ml_results = identify_product(filepath)

            if ml_results["status"] == "success":
                keyword = ml_results["analysis"]["category"]
                price_results = fetch_all_prices(keyword)
            else:
                price_results = []
            
            # 4. Return the ultimate combined response!
            return jsonify({
                "status": "success",
                "analysis": ml_results,
                "price_results": price_results
            }), 201
            
        except Exception as e:
            return jsonify({"status": "error", "message": f"Processing failed: {str(e)}"}), 500

# Global Error Handler: Triggers automatically if a file exceeds 10MB
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "status": "error", 
        "message": "File exceeds the 10MB size limit."
    }), 413

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)