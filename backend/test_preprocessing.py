import unittest
import numpy as np
import cv2
import os
from preprocessing import process_image

class TestImagePreprocessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Runs once before all tests to create a temporary test image."""
        cls.test_image_path = 'temp_test_image.jpg'
        # Create a random noisy image (500x500 pixels, 3 color channels)
        dummy_img = np.random.randint(0, 256, (500, 500, 3), dtype=np.uint8)
        cv2.imwrite(cls.test_image_path, dummy_img)

    @classmethod
    def tearDownClass(cls):
        """Runs once after all tests to clean up."""
        if os.path.exists(cls.test_image_path):
            os.remove(cls.test_image_path)

    def test_output_dimensions(self):
        """Tests if the image is correctly resized to 224x224 with 3 RGB channels."""
        img_normalized, _ = process_image(self.test_image_path, target_size=(224, 224))
        self.assertEqual(img_normalized.shape, (224, 224, 3))

    def test_normalization_range(self):
        """Tests if the pixel values are correctly scaled between 0.0 and 1.0."""
        img_normalized, _ = process_image(self.test_image_path)
        self.assertTrue(np.max(img_normalized) <= 1.0)
        self.assertTrue(np.min(img_normalized) >= 0.0)
        self.assertEqual(img_normalized.dtype, np.float32)

    def test_invalid_image_path(self):
        """Tests if the function properly catches bad file paths."""
        with self.assertRaises(ValueError):
            process_image('this_file_does_not_exist.jpg')

if __name__ == '__main__':
    unittest.main()