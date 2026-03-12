import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // ⚠️ Update this to your CURRENT Codespace public URL
  const API_URL = "https://crispy-bassoon-wr659rpv7p752vv79-5000.app.github.dev/";

  const onFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (!selectedFile) return;

    if (!selectedFile.type.startsWith("image/")) {
      setError("Please upload a valid image file.");
      return;
    }

    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setError(null);
    setData(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a product image first.");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("image", file);

    try {
      const response = await axios.post(
        `${API_URL}/api/upload-image`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      if (response.data.status === "success") {
        setData(response.data);
      } else {
        setError(response.data.message || "Unexpected response from server.");
      }
    } catch (err) {
      setError(
        "Connection Error: Make sure Flask server is running and Port 5000 is Public."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 font-sans">
      <div className="max-w-3xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-2">
            Price Oracle AI
          </h1>
          <p className="text-lg text-gray-600">
            AI Powered Product Recognition & Price Comparison
          </p>
        </header>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Upload Section */}
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl p-6">
            {preview ? (
              <img
                src={preview}
                alt="Preview"
                className="h-64 w-full object-contain mb-4 rounded-lg shadow-sm"
              />
            ) : (
              <div className="text-gray-400 mb-4 text-center">
                <p className="text-4xl mb-2">📸</p>
                <p>No image selected</p>
              </div>
            )}

            <input
              type="file"
              onChange={onFileChange}
              className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-indigo-50 file:text-indigo-700
              hover:file:bg-indigo-100"
            />
          </div>

          <button
            onClick={handleUpload}
            disabled={loading}
            className={`w-full mt-6 py-4 rounded-xl text-lg font-bold text-white transition-all shadow-lg ${
              loading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-700 active:scale-95"
            }`}
          >
            {loading ? "Analyzing Product..." : "Identify & Compare Prices"}
          </button>

          {/* Error Alert */}
          {error && (
            <div className="mt-6 bg-red-50 border-l-4 border-red-400 p-4 rounded-md">
              <p className="text-sm text-red-700 font-medium">{error}</p>
            </div>
          )}

          {/* Results Section */}
          {data && (
            <div className="mt-10 border-t pt-8 animate-fadeIn">
              {/* AI Result */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-indigo-50 p-6 rounded-2xl border border-indigo-100">
                  <span className="text-xs font-bold text-indigo-500 uppercase tracking-widest">
                    Identified Category
                  </span>
                  <p className="text-3xl font-black text-indigo-900 mt-1">
                    {data.analysis.analysis.category}
                  </p>
                </div>

                <div className="bg-green-50 p-6 rounded-2xl border border-green-100">
                  <span className="text-xs font-bold text-green-500 uppercase tracking-widest">
                    System Confidence
                  </span>
                  <p className="text-3xl font-black text-green-900 mt-1">
                    {data.analysis.analysis.confidence}%
                  </p>
                </div>
              </div>

              {/* Keywords */}
              <div className="mt-6">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                  Search Keywords
                </span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {data.analysis.keywords &&
                    data.analysis.keywords.map((word, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-white border border-gray-200 text-gray-600 rounded-full text-sm shadow-sm"
                      >
                        #{word}
                      </span>
                    ))}
                </div>
              </div>

              {/* Price Results */}
              {data.price_results && data.price_results.length > 0 && (
                <div className="mt-8">
                  <h2 className="text-xl font-bold mb-4">
                    Price Comparison
                  </h2>

                  {data.price_results.map((item, i) => (
                    <div
                      key={i}
                      className="mb-4 p-4 bg-white rounded-xl shadow border"
                    >
                      <p className="font-semibold">{item.name}</p>
                      <p className="text-green-600 font-bold">
                        ₹ {item.price}
                      </p>
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-500 underline text-sm"
                      >
                        View on {item.store}
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;