import cv2
import numpy as np

def process_image(image_path, target_size=(224, 224)):
    """
    Complete image preprocessing pipeline for CNN models.
    Takes an image path and returns the normalized array and the enhanced image.
    """
    # 1. Load the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image at {image_path}. File may be corrupted or missing.")

    # 2. Convert to consistent format (RGB)
    # OpenCV loads images in BGR format by default, but most ML models expect RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 3. Resize to standard dimensions
    # 224x224 is the standard input size for ResNet, MobileNet, and VGG models
    img_resized = cv2.resize(img_rgb, target_size)

    # 4. Noise Reduction (Gaussian Blur)
    # A 3x3 kernel removes high-frequency noise without blurring the edges too much
    img_blurred = cv2.GaussianBlur(img_resized, (3, 3), 0)

    # 5. Image Enhancement (Contrast and Brightness)
    # alpha = contrast control (1.2 adds 20% contrast), beta = brightness control (10 adds slight brightness)
    img_enhanced = cv2.convertScaleAbs(img_blurred, alpha=1.2, beta=10)

    # 6. Normalization
    # Scale pixel values from standard 0-255 down to 0.0-1.0 (Crucial for neural network gradients)
    img_normalized = img_enhanced.astype('float32') / 255.0

    # We return the normalized array for the ML model, and the enhanced image if we want to save/view it
    return img_normalized, img_enhanced