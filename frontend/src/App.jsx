import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import './App.css';

function getDefaultApiBaseUrl() {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL.replace(/\/$/, '');
  }

  if (typeof window !== 'undefined') {
    const { hostname, protocol } = window.location;

    if (hostname.includes('app.github.dev')) {
      return `${protocol}//${hostname.replace(/-\d+\./, '-5000.')}`;
    }

    return 'http://127.0.0.1:5000';
  }

  return 'http://127.0.0.1:5000';
}

const API_BASE_URL = getDefaultApiBaseUrl();
const AUTO_REFRESH_MS = 60000;

const emptyAnalysis = {
  analysis: {
    category: 'Not identified',
    confidence: 0,
  },
  keywords: [],
};

const availabilityRank = {
  'In stock': 3,
  'Limited stock': 2,
  Preorder: 1,
  'Out of stock': 0,
  Unknown: 0,
};

const priceBands = [
  { label: 'All prices', value: 'all' },
  { label: 'Under Rs 25,000', value: 'under-25000' },
  { label: 'Rs 25,000 to Rs 50,000', value: '25000-50000' },
  { label: 'Rs 50,000+', value: '50000-plus' },
];

const shippingFilters = [
  { label: 'Any shipping', value: 'all' },
  { label: 'Free shipping', value: 'free' },
  { label: 'Pickup', value: 'pickup' },
  { label: 'Standard shipping', value: 'standard' },
];

function buildApiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

function formatPrice(price) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(price || 0);
}

function formatReviews(reviewCount) {
  if (!reviewCount) {
    return 'No review volume';
  }

  return `${reviewCount.toLocaleString()} reviews`;
}

function normalizeResult(item, index, fallbackImage) {
  const parsedPrice =
    typeof item.price === 'number'
      ? item.price
      : Number.parseFloat(String(item.price || '0').replace(/[^0-9.]/g, ''));
  const shipping = item.shipping || 'Standard shipping';
  const shippingType =
    item.shippingType ||
    (shipping.toLowerCase().includes('pickup')
      ? 'pickup'
      : shipping.toLowerCase().includes('free')
        ? 'free'
        : 'standard');

  return {
    id: item.id || `${item.store || 'store'}-${index + 1}`,
    name: item.name || item.product_name || 'Matched product',
    price: Number.isFinite(parsedPrice) ? parsedPrice : 0,
    store: item.store || `Store ${index + 1}`,
    url: item.url || '#',
    image: item.image || fallbackImage || '',
    rating: item.rating || null,
    reviewCount: item.reviewCount || item.review_count || null,
    availability: item.availability || 'Unknown',
    shipping,
    shippingType,
    trust: item.trust || item.trustIndicators || ['Verified seller'],
  };
}

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [pricesLoading, setPricesLoading] = useState(false);
  const [refreshingPrices, setRefreshingPrices] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [networkError, setNetworkError] = useState(null);
  const [shareStatus, setShareStatus] = useState(null);
  const [sortBy, setSortBy] = useState('price');
  const [priceRange, setPriceRange] = useState('all');
  const [shippingFilter, setShippingFilter] = useState('all');
  const [selectedStores, setSelectedStores] = useState([]);
  const [viewMode, setViewMode] = useState('cards');
  const [activeProduct, setActiveProduct] = useState('');
  const [isDragActive, setIsDragActive] = useState(false);

  const fetchPriceHistory = useCallback(async (productId) => {
    if (!productId) {
      setPriceHistory([]);
      return;
    }

    try {
      const response = await axios.get(buildApiUrl('/api/price-history'), {
        params: { product_id: productId, page_size: 6 },
      });
      setPriceHistory(response.data.history || []);
    } catch {
      setPriceHistory([]);
    }
  }, []);

  const fetchComparison = useCallback(
    async (product, { forceRefresh = false, silent = false, productId = null } = {}) => {
      if (!product) {
        return;
      }

      if (silent) {
        setRefreshingPrices(true);
      } else {
        setPricesLoading(true);
        setNetworkError(null);
      }

      try {
        const response = await axios.get(buildApiUrl('/api/compare-prices'), {
          params: {
            product,
            page_size: 20,
            force_refresh: forceRefresh,
          },
        });

        setComparisonData(response.data);
        setActiveProduct(response.data.product || product);
        await fetchPriceHistory(response.data.product_id || productId);
      } catch (error) {
        setNetworkError(
          error.response?.data?.message ||
            `Unable to retrieve price comparisons from ${API_BASE_URL}.`
        );
      } finally {
        setPricesLoading(false);
        setRefreshingPrices(false);
      }
    },
    [fetchPriceHistory]
  );

  useEffect(() => {
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const linkedProduct = query.get('product');
    const linkedView = query.get('view');

    if (linkedView === 'table' || linkedView === 'cards') {
      setViewMode(linkedView);
    }

    if (linkedProduct) {
      setActiveProduct(linkedProduct);
      fetchComparison(linkedProduct);
    }
  }, [fetchComparison]);

  useEffect(() => {
    if (!activeProduct) {
      return undefined;
    }

    const refreshId = window.setInterval(() => {
      fetchComparison(activeProduct, { silent: true, forceRefresh: true });
    }, AUTO_REFRESH_MS);

    return () => window.clearInterval(refreshId);
  }, [activeProduct, fetchComparison]);

  useEffect(() => {
    const url = new URL(window.location.href);

    if (activeProduct) {
      url.searchParams.set('product', activeProduct);
      url.searchParams.set('view', viewMode);
    } else {
      url.searchParams.delete('product');
      url.searchParams.delete('view');
    }

    window.history.replaceState({}, '', url);
  }, [activeProduct, viewMode]);

  useEffect(() => {
    setSelectedStores([]);
  }, [comparisonData]);

  const applySelectedFile = useCallback((selectedFile) => {
    if (!selectedFile) {
      return;
    }

    if (!selectedFile.type.startsWith('image/')) {
      setNetworkError('Please upload a valid image file.');
      return;
    }

    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setNetworkError(null);
    setComparisonData(null);
    setUploadResult(null);
    setPriceHistory([]);
    setActiveProduct('');
    setIsDragActive(false);
  }, [preview]);

  const onFileChange = (event) => {
    applySelectedFile(event.target.files?.[0]);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    if (!isDragActive) {
      setIsDragActive(true);
    }
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    if (event.currentTarget.contains(event.relatedTarget)) {
      return;
    }
    setIsDragActive(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragActive(false);
    applySelectedFile(event.dataTransfer.files?.[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setNetworkError('Please select a product image first.');
      return;
    }

    setUploadLoading(true);
    setNetworkError(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await axios.post(buildApiUrl('/api/upload-image'), formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setUploadResult(response.data);
      const productName = response.data.analysis?.analysis?.category;
      setActiveProduct(productName || '');

      if (productName) {
        await fetchComparison(productName, { productId: response.data.product_id });
      }
    } catch (error) {
      setNetworkError(
        error.response?.data?.message ||
          `Upload failed. The frontend could not reach ${API_BASE_URL}.`
      );
    } finally {
      setUploadLoading(false);
    }
  };

  const handleRefresh = async () => {
    await fetchComparison(activeProduct, { forceRefresh: true, silent: true });
  };

  const handleCopyLink = async () => {
    if (!activeProduct) {
      return;
    }

    try {
      await navigator.clipboard.writeText(window.location.href);
      setShareStatus('Share link copied.');
    } catch {
      setShareStatus('Unable to copy the share link.');
    }

    window.setTimeout(() => setShareStatus(null), 2000);
  };

  const liveAnalysis = uploadResult?.analysis || emptyAnalysis;
  const normalizedResults = (comparisonData?.offers || []).map((item, index) =>
    normalizeResult(item, index, preview)
  );
  const availableStores = Array.from(new Set(normalizedResults.map((item) => item.store)));
  const activeStores = selectedStores.length > 0 ? selectedStores : availableStores;

  const filteredResults = useMemo(
    () =>
      normalizedResults
        .filter((item) => activeStores.includes(item.store))
        .filter((item) => {
          if (priceRange === 'under-25000') {
            return item.price < 25000;
          }
          if (priceRange === '25000-50000') {
            return item.price >= 25000 && item.price <= 50000;
          }
          if (priceRange === '50000-plus') {
            return item.price > 50000;
          }
          return true;
        })
        .filter((item) => (shippingFilter === 'all' ? true : item.shippingType === shippingFilter))
        .sort((left, right) => {
          if (sortBy === 'rating') {
            return (right.rating || 0) - (left.rating || 0);
          }
          if (sortBy === 'availability') {
            return (
              (availabilityRank[right.availability] || 0) -
              (availabilityRank[left.availability] || 0)
            );
          }
          return left.price - right.price;
        }),
    [activeStores, normalizedResults, priceRange, shippingFilter, sortBy]
  );

  const bestDeal =
    filteredResults.length > 0
      ? filteredResults.reduce((best, current) => (current.price < best.price ? current : best))
      : null;

  const toggleStore = (store) => {
    setSelectedStores((currentStores) =>
      currentStores.includes(store)
        ? currentStores.filter((item) => item !== store)
        : [...currentStores, store]
    );
  };

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <main className="app-frame">
        <section className="hero-panel">
          <div className="hero-copy">
            <span className="eyebrow">Price Oracle AI</span>
          </div>

          <div
            className={isDragActive ? 'upload-panel drag-active' : 'upload-panel'}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {!preview ? <p className="upload-hint">Upload a product image</p> : null}
            <div className="upload-preview">
              {preview ? (
                <img src={preview} alt="Uploaded product preview" />
              ) : (
                <div className="preview-placeholder">
                  <div className="upload-symbol">+</div>
                  <span>Drop an image here or browse from your device.</span>
                </div>
              )}
            </div>

            <label className="file-picker">
              <span className="file-picker-label">
                <span className="file-picker-plus">+</span>
                <span>Choose File</span>
              </span>
              <input type="file" accept="image/png,image/jpeg,image/webp" onChange={onFileChange} />
            </label>

            <button
              type="button"
              onClick={handleUpload}
              disabled={uploadLoading}
              className="primary-button"
            >
              {uploadLoading ? 'Identifying product...' : 'Identify and compare prices'}
            </button>

            {networkError ? <p className="status-message error">{networkError}</p> : null}
          </div>

          <div className="hero-metrics">
            <article>
              <span>Category</span>
              <strong>{liveAnalysis.analysis.category}</strong>
            </article>
            <article>
              <span>Confidence</span>
              <strong>{liveAnalysis.analysis.confidence}%</strong>
            </article>
            <article>
              <span>Tracked offers</span>
              <strong>{filteredResults.length}</strong>
            </article>
          </div>
        </section>

        <section className="results-shell">
          <div className="results-header">
            <div>
              <span className="eyebrow">Comparison Results</span>
              <h2>{activeProduct || 'No product selected yet'}</h2>
              <div className="keyword-row">
                {liveAnalysis.keywords.map((word) => (
                  <span key={word} className="keyword-pill">
                    #{word}
                  </span>
                ))}
              </div>
            </div>

            <div className="results-actions">
              <div className="view-toggle" role="tablist" aria-label="Display mode">
                <button
                  type="button"
                  className={viewMode === 'cards' ? 'active' : ''}
                  onClick={() => setViewMode('cards')}
                >
                  Cards
                </button>
                <button
                  type="button"
                  className={viewMode === 'table' ? 'active' : ''}
                  onClick={() => setViewMode('table')}
                >
                  Table
                </button>
              </div>

              <div className="action-row">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleRefresh}
                  disabled={!activeProduct || refreshingPrices}
                >
                  {refreshingPrices ? 'Refreshing...' : 'Refresh prices'}
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleCopyLink}
                  disabled={!activeProduct}
                >
                  Copy share link
                </button>
              </div>
            </div>
          </div>

          {comparisonData ? (
            <>
              <div className="summary-grid">
                <article>
                  <span>Best store</span>
                  <strong>{comparisonData.summary.best_store || 'Pending'}</strong>
                </article>
                <article>
                  <span>Lowest price</span>
                  <strong>{formatPrice(comparisonData.summary.lowest_price || 0)}</strong>
                </article>
                <article>
                  <span>Average price</span>
                  <strong>{formatPrice(comparisonData.summary.average_price || 0)}</strong>
                </article>
                <article>
                  <span>Cache</span>
                  <strong>{comparisonData.cache.hit ? 'Warm cache' : 'Fresh query'}</strong>
                </article>
              </div>

              <div className="toolbar">
                <label>
                  <span>Sort by</span>
                  <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
                    <option value="price">Price</option>
                    <option value="rating">Rating</option>
                    <option value="availability">Availability</option>
                  </select>
                </label>

                <label>
                  <span>Price range</span>
                  <select value={priceRange} onChange={(event) => setPriceRange(event.target.value)}>
                    {priceBands.map((band) => (
                      <option key={band.value} value={band.value}>
                        {band.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  <span>Shipping</span>
                  <select
                    value={shippingFilter}
                    onChange={(event) => setShippingFilter(event.target.value)}
                  >
                    {shippingFilters.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="store-filter-row">
                {availableStores.map((store) => {
                  const active = activeStores.includes(store);

                  return (
                    <button
                      key={store}
                      type="button"
                      className={active ? 'store-chip active' : 'store-chip'}
                      onClick={() => toggleStore(store)}
                    >
                      {store}
                    </button>
                  );
                })}
              </div>
            </>
          ) : null}

          {shareStatus ? <p className="status-message muted">{shareStatus}</p> : null}
          {comparisonData ? (
            <p className="status-message muted">
              Auto-refresh is active every 60 seconds while this result stays open.
            </p>
          ) : null}

          {pricesLoading ? (
            <div className="results-grid skeleton-grid">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={`skeleton-${index}`} className="deal-card skeleton-card">
                  <div className="skeleton-block media" />
                  <div className="card-content">
                    <div className="skeleton-block line short" />
                    <div className="skeleton-block line" />
                    <div className="skeleton-block line" />
                    <div className="skeleton-block button" />
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          {!pricesLoading && !comparisonData ? (
            <div className="empty-state">
              <h3>No comparison results yet.</h3>
              <p>Upload a product image to identify the product and fetch live store offers.</p>
            </div>
          ) : null}

          {!pricesLoading && comparisonData && filteredResults.length === 0 ? (
            <div className="empty-state">
              <h3>No offers match the current filters.</h3>
              <p>Adjust the selected stores, price range, or shipping options.</p>
            </div>
          ) : null}

          {!pricesLoading && viewMode === 'cards' && filteredResults.length > 0 ? (
            <div className="results-grid">
              {filteredResults.map((item) => {
                const isBestDeal = bestDeal?.id === item.id;

                return (
                  <article
                    key={item.id}
                    className={isBestDeal ? 'deal-card best-deal' : 'deal-card'}
                  >
                    <div className="card-media">
                      {item.image ? <img src={item.image} alt={item.name} /> : <div className="preview-placeholder"><span>No product image</span></div>}
                      {isBestDeal ? <span className="deal-badge">Best deal</span> : null}
                    </div>

                    <div className="card-content">
                      <div className="store-line">
                        <div className="store-logo" aria-hidden="true">
                          {item.store
                            .split(' ')
                            .map((part) => part[0])
                            .join('')
                            .slice(0, 2)}
                        </div>
                        <div>
                          <p className="store-name">{item.store}</p>
                          <p className="availability">{item.availability}</p>
                        </div>
                      </div>

                      <h3>{item.name}</h3>

                      <div className="price-row">
                        <strong>{formatPrice(item.price)}</strong>
                        <span>{item.shipping}</span>
                      </div>

                      <div className="meta-row">
                        <span>Rating {item.rating ? `${item.rating}/5` : 'N/A'}</span>
                        <span>{formatReviews(item.reviewCount)}</span>
                      </div>

                      <div className="trust-row">
                        {item.trust.map((badge) => (
                          <span key={badge} className="trust-pill">
                            {badge}
                          </span>
                        ))}
                      </div>

                      <a href={item.url} target="_blank" rel="noreferrer" className="deal-button">
                        View Deal
                      </a>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : null}

          {!pricesLoading && viewMode === 'table' && filteredResults.length > 0 ? (
            <div className="table-shell">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>Store</th>
                    <th>Offer</th>
                    <th>Price</th>
                    <th>Rating</th>
                    <th>Availability</th>
                    <th>Shipping</th>
                    <th>Trust</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {filteredResults.map((item) => {
                    const isBestDeal = bestDeal?.id === item.id;

                    return (
                      <tr key={item.id} className={isBestDeal ? 'table-best-deal' : ''}>
                        <td>
                          <div className="table-store">
                            <div className="store-logo" aria-hidden="true">
                              {item.store
                                .split(' ')
                                .map((part) => part[0])
                                .join('')
                                .slice(0, 2)}
                            </div>
                            <span>{item.store}</span>
                          </div>
                        </td>
                        <td>{item.name}</td>
                        <td>{formatPrice(item.price)}</td>
                        <td>{item.rating ? `${item.rating}/5` : 'N/A'}</td>
                        <td>{item.availability}</td>
                        <td>{item.shipping}</td>
                        <td>{item.trust.join(', ')}</td>
                        <td>
                          <a href={item.url} target="_blank" rel="noreferrer" className="table-link">
                            View Deal
                          </a>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : null}

          <div className="history-panel">
            <div className="history-header">
              <h3>Recent Price History</h3>
              <span>{priceHistory.length > 0 ? 'Stored snapshots from the backend' : 'No stored history yet'}</span>
            </div>
            <div className="history-list">
              {priceHistory.length > 0 ? (
                priceHistory.map((entry) => (
                  <article key={entry.price_id} className="history-item">
                    <strong>{entry.store_name}</strong>
                    <span>{formatPrice(entry.price)}</span>
                    <time>{new Date(entry.timestamp).toLocaleString()}</time>
                  </article>
                ))
              ) : (
                <p className="status-message muted">
                  Fetch a live product comparison to persist and display history snapshots.
                </p>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
