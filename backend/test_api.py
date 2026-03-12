import unittest
from unittest.mock import patch

import app as backend_app
from database import Price, Product, db


class ApiEndpointTests(unittest.TestCase):
    def setUp(self):
        backend_app.app.config['TESTING'] = True
        self.client = backend_app.app.test_client()

        with backend_app.app.app_context():
            db.drop_all()
            db.create_all()

        backend_app.rate_limit_log.clear()
        backend_app.comparison_cache.clear()

    def tearDown(self):
        with backend_app.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_compare_prices_endpoint_returns_paginated_results(self):
        with backend_app.app.app_context():
            product = Product(name='Headphones', category='headphones', image_url='')
            db.session.add(product)
            db.session.commit()

        payload = {
            'product': 'Headphones',
            'offers': [
                {
                    'store': 'Amazon',
                    'name': 'Headphones',
                    'price': 100.0,
                    'price_display': '$100.00',
                    'url': 'https://example.com/amazon',
                    'availability': 'In stock',
                    'shipping': 'Free shipping',
                    'shipping_cost': 0.0,
                    'shippingType': 'free',
                    'rating': 4.8,
                    'reviewCount': 120,
                    'image': None,
                    'trust': ['Verified seller'],
                    'rank': 1,
                },
                {
                    'store': 'Best Buy',
                    'name': 'Headphones',
                    'price': 120.0,
                    'price_display': '$120.00',
                    'url': 'https://example.com/bestbuy',
                    'availability': 'Limited stock',
                    'shipping': 'Pickup today',
                    'shipping_cost': 0.0,
                    'shippingType': 'pickup',
                    'rating': 4.6,
                    'reviewCount': 98,
                    'image': None,
                    'trust': ['Top-rated store'],
                    'rank': 2,
                },
            ],
            'summary': {
                'lowest_price': 100.0,
                'highest_price': 120.0,
                'average_price': 110.0,
                'best_store': 'Amazon',
                'offer_count': 2,
            },
            'generated_at': '2026-03-12T00:00:00Z',
        }

        with patch('app.fetch_comparison_data', return_value=(payload, False)):
            response = self.client.get('/api/compare-prices?product=Headphones&page=1&page_size=1')

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['status'], 'success')
        self.assertEqual(body['product'], 'Headphones')
        self.assertEqual(len(body['offers']), 1)
        self.assertEqual(body['pagination']['total_pages'], 2)
        self.assertEqual(body['product_id'], 1)
        self.assertFalse(body['cache']['hit'])

    def test_price_history_endpoint_returns_saved_records(self):
        with backend_app.app.app_context():
            product = Product(name='Laptop', category='laptop', image_url='demo.jpg')
            db.session.add(product)
            db.session.commit()
            product_id = product.product_id

            db.session.add(
                Price(
                    product_id=product.product_id,
                    store_name='Amazon',
                    price=1499.0,
                    product_url='https://example.com/laptop',
                )
            )
            db.session.commit()

        response = self.client.get(f'/api/price-history?product_id={product_id}')

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['status'], 'success')
        self.assertEqual(body['product']['name'], 'Laptop')
        self.assertEqual(len(body['history']), 1)
        self.assertEqual(body['history'][0]['store_name'], 'Amazon')

    def test_upload_image_rejects_invalid_format(self):
        with open(__file__, 'rb') as file_handle:
            response = self.client.post(
                '/api/upload-image',
                data={'image': (file_handle, 'test.txt')},
                content_type='multipart/form-data',
            )

        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertEqual(body['status'], 'error')


if __name__ == '__main__':
    unittest.main()
