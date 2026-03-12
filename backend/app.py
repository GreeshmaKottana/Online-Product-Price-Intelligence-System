import os
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime
from functools import wraps

import cv2
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from crud import create_price, create_product, save_search
from database import Price, Product, SearchHistory, db

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
CACHE_TTL_SECONDS = int(os.getenv('COMPARE_CACHE_TTL', '300'))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('RATE_LIMIT_WINDOW_SECONDS', '60'))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '30'))
DEFAULT_PAGE_SIZE = 6
MAX_PAGE_SIZE = 20

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    f"sqlite:///{os.path.join(BASE_DIR, 'price_oracle.db')}",
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()

comparison_cache = {}
rate_limit_log = defaultdict(deque)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_client_key():
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr or 'anonymous'


def rate_limited():
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            client_key = get_client_key()
            request_log = rate_limit_log[client_key]
            now = time.time()

            while request_log and now - request_log[0] > RATE_LIMIT_WINDOW_SECONDS:
              request_log.popleft()

            if len(request_log) >= RATE_LIMIT_MAX_REQUESTS:
                return (
                    jsonify(
                        {
                            'status': 'error',
                            'message': 'Rate limit exceeded. Please try again shortly.',
                        }
                    ),
                    429,
                )

            request_log.append(now)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def parse_positive_int(value, default):
    try:
        parsed = int(value)
        if parsed <= 0:
            return default
        return parsed
    except (TypeError, ValueError):
        return default


def normalize_product_name(name):
    return ' '.join((name or '').strip().lower().split())


def clean_price_value(raw_price):
    if raw_price is None:
        return None

    if isinstance(raw_price, (int, float)):
        return round(float(raw_price), 2)

    price_string = str(raw_price).replace(',', '')
    filtered = ''.join(char for char in price_string if char.isdigit() or char == '.')

    if not filtered:
        return None

    try:
        return round(float(filtered), 2)
    except ValueError:
        return None


def extract_shipping_cost(raw_shipping):
    if raw_shipping is None:
        return 0.0

    if isinstance(raw_shipping, (int, float)):
        return float(raw_shipping)

    shipping_text = str(raw_shipping).lower()
    if 'free' in shipping_text or 'pickup' in shipping_text:
        return 0.0

    return clean_price_value(raw_shipping) or 0.0


def serialize_offer(raw_offer, rank=None):
    price_value = clean_price_value(raw_offer.get('price'))
    shipping_text = raw_offer.get('shipping') or 'Standard shipping'
    shipping_cost = extract_shipping_cost(shipping_text)
    rating_value = raw_offer.get('rating')
    review_count = raw_offer.get('reviewCount') or raw_offer.get('review_count')

    try:
        rating_value = round(float(rating_value), 1) if rating_value not in (None, 'N/A') else None
    except (TypeError, ValueError):
        rating_value = None

    if review_count is not None:
        try:
            review_count = int(review_count)
        except (TypeError, ValueError):
            review_count = None

    shipping_type = raw_offer.get('shippingType')
    if not shipping_type:
        lowered_shipping = str(shipping_text).lower()
        if 'pickup' in lowered_shipping:
            shipping_type = 'pickup'
        elif 'free' in lowered_shipping:
            shipping_type = 'free'
        else:
            shipping_type = 'standard'

    return {
        'store': raw_offer.get('store') or 'Unknown store',
        'name': raw_offer.get('name') or raw_offer.get('product_name') or 'Matched product',
        'price': price_value,
        'price_display': raw_offer.get('price_display')
        or raw_offer.get('price')
        or (f'${price_value:.2f}' if price_value is not None else 'N/A'),
        'url': raw_offer.get('url') or '#',
        'availability': raw_offer.get('availability') or 'Unknown',
        'shipping': shipping_text,
        'shipping_cost': round(shipping_cost, 2),
        'shippingType': shipping_type,
        'rating': rating_value,
        'reviewCount': review_count,
        'image': raw_offer.get('image'),
        'trust': raw_offer.get('trust') or raw_offer.get('trustIndicators') or ['Verified seller'],
        'rank': rank,
    }


def paginate_items(items, page, page_size):
    total_items = len(items)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    page = min(max(page, 1), total_pages)
    start = (page - 1) * page_size
    end = start + page_size

    return items[start:end], {
        'page': page,
        'page_size': page_size,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1,
    }


def get_or_create_product_record(product_name, image_url=''):
    normalized_name = normalize_product_name(product_name)
    existing = Product.query.filter(Product.name.ilike(product_name)).first()

    if existing:
        if image_url and not existing.image_url:
            existing.image_url = image_url
            db.session.commit()
        return existing

    return create_product(name=product_name, category=normalized_name or product_name, image_url=image_url)


def persist_price_snapshot(product, offers):
    for offer in offers:
        if offer['price'] is None:
            continue

        create_price(
            product.product_id,
            offer['store'],
            offer['price'],
            offer['url'],
        )


def build_comparison_payload(product_name, offers, comparison):
    best_offer = min(
        (offer for offer in offers if offer['price'] is not None),
        key=lambda offer: offer['price'] + offer['shipping_cost'],
        default=None,
    )

    return {
        'product': product_name,
        'offers': offers,
        'summary': {
            'lowest_price': comparison.get('lowest_price'),
            'highest_price': comparison.get('highest_price'),
            'average_price': comparison.get('average_price'),
            'best_store': best_offer['store'] if best_offer else None,
            'offer_count': len(offers),
        },
        'generated_at': datetime.utcnow().isoformat() + 'Z',
    }


def fetch_comparison_data(product_name, force_refresh=False, image_url=''):
    from price_engine import compare_prices
    from scraper import fetch_all_prices

    normalized_name = normalize_product_name(product_name)
    cached_entry = comparison_cache.get(normalized_name)
    now = time.time()

    if (
        not force_refresh
        and cached_entry
        and now - cached_entry['timestamp'] < CACHE_TTL_SECONDS
    ):
        return cached_entry['payload'], True

    raw_results = fetch_all_prices(product_name)
    comparison = compare_prices(raw_results)
    offers = [
        serialize_offer(offer, rank=index + 1)
        for index, offer in enumerate(comparison.get('offers', []))
    ]

    payload = build_comparison_payload(product_name, offers, comparison)
    comparison_cache[normalized_name] = {'payload': payload, 'timestamp': now}

    product = get_or_create_product_record(product_name, image_url=image_url)
    persist_price_snapshot(product, offers)

    return payload, False


def build_compare_response(payload, cache_hit, page, page_size, product_id=None):
    paginated_offers, pagination = paginate_items(payload['offers'], page, page_size)

    response = {
        'status': 'success',
        'product': payload['product'],
        'summary': payload['summary'],
        'offers': paginated_offers,
        'pagination': pagination,
        'cache': {
            'hit': cache_hit,
            'ttl_seconds': CACHE_TTL_SECONDS,
            'generated_at': payload['generated_at'],
        },
    }

    if product_id is not None:
        response['product_id'] = product_id

    return response


OPENAPI_SPEC = {
    'openapi': '3.0.0',
    'info': {
        'title': 'Price Oracle API',
        'version': '1.0.0',
        'description': 'Image upload, product recognition, price comparison, and price history endpoints.',
    },
    'paths': {
        '/api/upload-image': {
            'post': {
                'summary': 'Upload a product image and identify the product.',
            }
        },
        '/api/compare-prices': {
            'get': {
                'summary': 'Retrieve paginated comparison results for a product query.',
            }
        },
        '/api/price-history': {
            'get': {
                'summary': 'Retrieve historical stored prices for a product.',
            }
        },
    },
}


@app.route('/api/docs', methods=['GET'])
def api_docs():
    return jsonify(OPENAPI_SPEC)


@app.route('/api/health', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'ok'})


@app.route('/api/upload-image', methods=['POST'])
@rate_limited()
def upload_image():
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image uploaded.'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Empty filename.'}), 400

    if not allowed_file(file.filename):
        return jsonify(
            {
                'status': 'error',
                'message': 'Unsupported file format. Use JPEG, PNG, or WebP.',
            }
        ), 400

    image_id = str(uuid.uuid4())
    extension = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(f'{image_id}.{extension}')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(filepath)

        from model_engine import identify_product
        from preprocessing import process_image

        _, image_enhanced = process_image(filepath)
        enhanced_filename = f'enhanced_{filename}'
        enhanced_filepath = os.path.join(app.config['UPLOAD_FOLDER'], enhanced_filename)
        cv2.imwrite(enhanced_filepath, cv2.cvtColor(image_enhanced, cv2.COLOR_RGB2BGR))

        identification = identify_product(filepath)
        if identification.get('status') != 'success':
            return jsonify({'status': 'error', 'message': 'AI prediction failed.'}), 500

        product_name = identification.get('analysis', {}).get('category')
        if not product_name:
            return jsonify({'status': 'error', 'message': 'Unable to identify product.'}), 422

        save_search('anonymous', product_name)
        product = get_or_create_product_record(product_name, image_url=filename)

        return (
            jsonify(
                {
                    'status': 'success',
                    'image_id': image_id,
                    'product_id': product.product_id,
                    'analysis': identification,
                    'upload': {
                        'filename': filename,
                        'enhanced_filename': enhanced_filename,
                    },
                }
            ),
            201,
        )
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/compare-prices', methods=['GET'])
@rate_limited()
def compare_prices_endpoint():
    product_name = request.args.get('product', '').strip()
    if not product_name:
        return jsonify({'status': 'error', 'message': 'Query parameter "product" is required.'}), 400

    page = parse_positive_int(request.args.get('page'), 1)
    page_size = min(parse_positive_int(request.args.get('page_size'), DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE)
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

    try:
        payload, cache_hit = fetch_comparison_data(product_name, force_refresh=force_refresh)
        product = Product.query.filter(Product.name.ilike(product_name)).first()
        response = build_compare_response(
            payload,
            cache_hit=cache_hit,
            page=page,
            page_size=page_size,
            product_id=product.product_id if product else None,
        )
        return jsonify(response)
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/price-history', methods=['GET'])
def price_history():
    product_id = request.args.get('product_id')
    page = parse_positive_int(request.args.get('page'), 1)
    page_size = min(parse_positive_int(request.args.get('page_size'), 20), 50)

    if not product_id:
        return jsonify({'status': 'error', 'message': 'Query parameter "product_id" is required.'}), 400

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    records = (
        Price.query.filter_by(product_id=product.product_id)
        .order_by(Price.timestamp.desc())
        .all()
    )

    history_items = [
        {
            'price_id': record.price_id,
            'store_name': record.store_name,
            'price': record.price,
            'product_url': record.product_url,
            'timestamp': record.timestamp.isoformat() + 'Z',
        }
        for record in records
    ]

    paginated_records, pagination = paginate_items(history_items, page, page_size)

    return jsonify(
        {
            'status': 'success',
            'product': {
                'product_id': product.product_id,
                'name': product.name,
                'category': product.category,
                'image_url': product.image_url,
            },
            'history': paginated_records,
            'pagination': pagination,
        }
    )


@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.order_by(Product.product_id.desc()).all()
    result = [
        {
            'product_id': product.product_id,
            'name': product.name,
            'category': product.category,
            'image_url': product.image_url,
        }
        for product in products
    ]
    return jsonify(result)


@app.route('/api/prices/<int:product_id>', methods=['GET'])
def get_prices(product_id):
    prices = Price.query.filter_by(product_id=product_id).order_by(Price.timestamp.desc()).all()
    result = [
        {
            'store': price.store_name,
            'price': price.price,
            'timestamp': price.timestamp.isoformat() + 'Z',
            'url': price.product_url,
        }
        for price in prices
    ]
    return jsonify(result)


@app.route('/api/search-history', methods=['GET'])
def get_search_history():
    searches = SearchHistory.query.order_by(SearchHistory.timestamp.desc()).all()
    result = [
        {
            'search_id': search.search_id,
            'user_id': search.user_id,
            'query': search.query,
            'timestamp': search.timestamp.isoformat() + 'Z',
        }
        for search in searches
    ]
    return jsonify(result)


@app.route('/api/search-history/<int:search_id>', methods=['DELETE'])
def delete_search(search_id):
    search = db.session.get(SearchHistory, search_id)
    if not search:
        return jsonify({'error': 'Search not found'}), 404

    db.session.delete(search)
    db.session.commit()

    return jsonify({'message': 'Search deleted successfully'})


@app.errorhandler(413)
def request_entity_too_large(_error):
    return (
        jsonify(
            {
                'status': 'error',
                'message': 'File exceeds the 10MB size limit.',
            }
        ),
        413,
    )


if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)
