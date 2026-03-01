import os
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Enable CORS so the React frontend can talk to this API
CORS(app)

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
            # Store the image temporarily
            file.save(filepath)
            
            # Return success response with the unique ID
            return jsonify({
                "status": "success",
                "message": "Image uploaded successfully",
                "image_id": image_id,
                "filename": secure_name
            }), 201 # HTTP 201: Created
            
        except Exception as e:
            return jsonify({"status": "error", "message": f"Could not save file: {str(e)}"}), 500

# Global Error Handler: Triggers automatically if a file exceeds 10MB
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "status": "error", 
        "message": "File exceeds the 10MB size limit."
    }), 413

if __name__ == '__main__':
    app.run(debug=True, port=5000)