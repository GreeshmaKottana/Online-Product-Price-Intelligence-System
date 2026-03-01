import React from 'react';
import ImageUpload from './components/ImageUpload';

function App() {
  return (
    <div className="min-h-screen bg-[#F9FAFB] text-gray-900 font-sans">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </div>
            <span className="text-lg font-bold tracking-tight text-gray-900">Price Oracle</span>
          </div>
          <div className="hidden md:flex space-x-8 text-sm font-medium text-gray-500">
            <a href="#" className="text-blue-600">Search</a>
            <a href="#" className="hover:text-gray-900 transition-colors">History</a>
            <a href="#" className="hover:text-gray-900 transition-colors">Settings</a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          
          {/* Action Card */}
          <div className="lg:col-span-5">
            <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-xl shadow-gray-200/50">
              <h2 className="text-2xl font-bold mb-2">Visual Search</h2>
              <p className="text-gray-500 mb-8 text-sm leading-relaxed">
                Found something you love? Upload a photo and let the Oracle find the absolute lowest price across 50+ retailers.
              </p>
              <ImageUpload />
            </div>
          </div>

          {/* Results Placeholder / Visual Feedback */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-blue-50/50 border border-blue-100 rounded-3xl p-8 flex flex-col items-center justify-center min-h-[400px] text-center">
              <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
              </div>
              <h3 className="text-lg font-semibold text-blue-900">Awaiting Product Analysis</h3>
              <p className="text-blue-700/60 max-w-xs mt-2 text-sm">
                Once you upload an image, the AI will identify the product and display real-time price comparisons here.
              </p>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default App;