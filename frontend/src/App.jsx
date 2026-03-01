import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // Update this to your LATEST Codespace URL from the Ports tab
  const API_URL = "https://crispy-bassoon-wr659rpv7p752vv79-5000.app.github.dev/";

  const onFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setError(null);
      setData(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a product image first.");
      return;
    }

    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await axios.post(`${API_URL}/api/upload-image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.status === "success") {
        setData(response.data);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError("Connection Error: Is the Flask server running and Port 5000 set to Public?");
    } finally {
      setLoading(false);
    }
  };
  // 1. Add these handler functions inside your App component
const handleDragOver = (e) => {
  e.preventDefault(); // Essential to allow a drop
  e.stopPropagation();
};

const handleDrop = (e) => {
  e.preventDefault();
  e.stopPropagation();
  
  const droppedFile = e.dataTransfer.files[0];
  if (droppedFile && droppedFile.type.startsWith('image/')) {
    setFile(droppedFile);
    setPreview(URL.createObjectURL(droppedFile));
    setError(null);
    setData(null);
  } else {
    setError("Please drop a valid image file (JPG, PNG, WebP).");
  }
};

// 2. Update your Upload Section JSX to use them
<div 
  onDragOver={handleDragOver}
  onDrop={handleDrop}
  className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl p-6 transition-all hover:border-indigo-400 hover:bg-indigo-50 cursor-pointer"
>
  {preview ? (
    <img src={preview} alt="Preview" className="h-64 w-full object-contain mb-4 rounded-lg shadow-sm" />
  ) : (
    <div className="text-gray-400 mb-4 text-center">
      <p className="text-4xl mb-2">📥</p>
      <p>Drag & Drop your product image here</p>
      <p className="text-xs">or click to browse</p>
    </div>
  )}
  
  <input 
    type="file" 
    onChange={onFileChange} 
    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100" 
  />
</div>

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-3xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-2">Price Oracle AI</h1>
          <p className="text-lg text-gray-600">Task 6: Seamless Image-to-Product Intelligence</p>
        </header>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* UPLOAD SECTION */}
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl p-6 transition-all hover:border-indigo-400">
            {preview ? (
              <img src={preview} alt="Preview" className="h-64 w-full object-contain mb-4 rounded-lg shadow-sm" />
            ) : (
              <div className="text-gray-400 mb-4">📸 No image selected</div>
            )}
            
            <input type="file" onChange={onFileChange} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100" />
          </div>

          <button
            onClick={handleUpload}
            disabled={loading}
            className={`w-full mt-6 py-4 rounded-xl text-lg font-bold text-white transition-all shadow-lg ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 active:scale-95'}`}
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin h-5 w-5 mr-3 text-white" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Analyzing with ResNet50...
              </span>
            ) : "Identify & Compare Prices"}
          </button>

          {/* ERROR ALERT */}
          {error && (
            <div className="mt-6 bg-red-50 border-l-4 border-red-400 p-4 rounded-md">
              <div className="flex">
                <div className="ml-3"><p className="text-sm text-red-700 font-medium">{error}</p></div>
              </div>
            </div>
          )}

          {/* RESULTS GRID */}
          {data && (
            <div className="mt-10 border-t pt-8 animate-fadeIn">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-indigo-50 p-6 rounded-2xl border border-indigo-100">
                  <span className="text-xs font-bold text-indigo-500 uppercase tracking-widest">Identified Category</span>
                  <p className="text-3xl font-black text-indigo-900 mt-1">{data.analysis.analysis.category}</p>
                </div>
                <div className="bg-green-50 p-6 rounded-2xl border border-green-100">
                  <span className="text-xs font-bold text-green-500 uppercase tracking-widest">System Confidence</span>
                  <p className="text-3xl font-black text-green-900 mt-1">{data.analysis.analysis.confidence}%</p>
                </div>
              </div>

              <div className="mt-6">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Search Keywords</span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {data.analysis.keywords.map((word, i) => (
                    <span key={i} className="px-3 py-1 bg-white border border-gray-200 text-gray-600 rounded-full text-sm shadow-sm hover:bg-indigo-50 transition-colors">#{word}</span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;