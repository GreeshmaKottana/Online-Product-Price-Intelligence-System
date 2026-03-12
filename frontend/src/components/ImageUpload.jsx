import React, { useState } from 'react';

export default function ImageUpload() {
  const [imagePreview, setImagePreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // Helper to process the file
  const handleFile = (file) => {
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  // Drag handlers
  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  return (
    <div className="space-y-4">
      <div 
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`relative group flex flex-col items-center justify-center w-full h-56 border-2 border-dashed rounded-2xl transition-all duration-200 cursor-pointer shadow-sm
          ${isDragging 
            ? 'border-blue-500 bg-blue-50/50 scale-[1.02]' 
            : 'border-gray-200 bg-gray-50 hover:bg-white hover:border-blue-400'
          }`}
      >
        <label className="flex flex-col items-center justify-center w-full h-full cursor-pointer">
          <div className="flex flex-col items-center justify-center py-6 text-center px-4">
            <div className={`p-3 bg-white rounded-full shadow-sm mb-3 transition-transform ${isDragging ? 'scale-110' : 'group-hover:scale-110'}`}>
              <svg className={`w-6 h-6 ${isDragging ? 'text-blue-500' : 'text-blue-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-sm font-medium text-gray-700">
              {isDragging ? "Drop to Scan" : "Drop your product photo here"}
            </p>
            <p className="text-xs text-gray-400 mt-1">Or click to browse (Max 5MB)</p>
          </div>
          <input 
            type="file" 
            className="hidden" 
            accept="image/*" 
            onChange={(e) => handleFile(e.target.files[0])} 
          />
        </label>
      </div>

      {imagePreview && (
        <div className="overflow-hidden rounded-xl border border-gray-100 shadow-sm animate-in fade-in zoom-in duration-300">
          <img src={imagePreview} alt="Preview" className="w-full h-40 object-cover" />
        </div>
      )}

      <button className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow-lg shadow-blue-100 transition-all active:scale-[0.98]">
        Scan for Best Price
      </button>
    </div>
  );
}
